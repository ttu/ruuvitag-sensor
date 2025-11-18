import asyncio
import logging
import os
import re
import sys
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from bleak import BleakClient, BleakGATTCharacteristic, BleakScanner
from bleak.backends.scanner import AdvertisementData, AdvertisementDataCallback, BLEDevice

from ruuvitag_sensor.adapters import BleCommunicationAsync
from ruuvitag_sensor.adapters.utils import rssi_to_hex
from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData

MAC_REGEX = "[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$"
RUUVI_HISTORY_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
RUUVI_HISTORY_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # Write
RUUVI_HISTORY_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # Read and notify


def _get_scanner(detection_callback: AdvertisementDataCallback, bt_device: str = ""):
    # NOTE: On Linux - bleak.exc.BleakError: passive scanning mode requires bluez or_patterns
    # NOTE: On macOS - bleak.exc.BleakError: macOS does not support passive scanning
    scanning_mode = "passive" if sys.platform.startswith("win") else "active"

    if "bleak_dev" in os.environ.get("RUUVI_BLE_ADAPTER", "").lower():
        from ruuvitag_sensor.adapters.development.dev_bleak_scanner import DevBleakScanner  # noqa: PLC0415

        return DevBleakScanner(detection_callback, scanning_mode)

    if bt_device:
        return BleakScanner(
            detection_callback=detection_callback,
            scanning_mode=scanning_mode,  # type: ignore[arg-type]
            adapter=bt_device,
        )

    return BleakScanner(detection_callback=detection_callback, scanning_mode=scanning_mode)  # type: ignore[arg-type]


queue = asyncio.Queue[tuple[str, str]]()

log = logging.getLogger(__name__)


class BleCommunicationBleak(BleCommunicationAsync):
    @staticmethod
    def _parse_data(data: bytes) -> str:
        # Bleak returns data in a different format than the nix_hci
        # adapter. Since the rest of the processing pipeline is
        # somewhat reliant on the additional data, add to the
        # beginning of the actual data:
        #
        # - An FF type marker with 9904 (Ruuvi manufacturer identifier)
        # - A length marker, covering the vendor specific data
        # - Another length marker, covering the length-marked
        #   vendor data.
        #
        # Thus extended, the result can be parsed by the rest of
        # the pipeline.
        #
        # TODO: This is kinda awkward, and should be handled better.
        formatted = f"FF9904{data.hex()}"
        formatted = f"{(len(formatted) >> 1):02x}{formatted}"
        formatted = f"{(len(formatted) >> 1):02x}{formatted}"
        return formatted

    @staticmethod
    async def get_data(blacklist: list[str] | None = None, bt_device: str = "") -> AsyncGenerator[MacAndRawData, None]:
        async def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            # On macOS device address is not a MAC address, but a system specific ID
            # https://github.com/hbldh/bleak/issues/140
            mac: str = device.address if re.match(MAC_REGEX, device.address.lower()) else ""
            if blacklist and mac in blacklist:
                log.debug("MAC blacklised: %s", mac)
                return

            # TODO: Do all RuuviTags have data in 1177?
            if 1177 not in advertisement_data.manufacturer_data:
                return

            log.debug("Received data: %s", advertisement_data)

            data = BleCommunicationBleak._parse_data(advertisement_data.manufacturer_data[1177])

            # Add RSSI to encoded data as hex. All adapters use a common decoder.
            data += rssi_to_hex(advertisement_data.rssi)
            await queue.put((mac, data))

        scanner = _get_scanner(detection_callback, bt_device)
        await scanner.start()

        log.debug("Bleak scanner started")

        try:
            while True:
                next_item: tuple[str, str] = await queue.get()
                yield next_item
        except KeyboardInterrupt:
            pass
        except GeneratorExit:
            pass
        except Exception as ex:
            log.info(ex)

        await scanner.stop()

        log.debug("Bleak scanner stopped")

    @staticmethod
    async def get_first_data(mac: str, bt_device: str = "") -> RawData:
        """
        NOTE: get_first_data does not work on macOS.

        macOS doesn't return MAC address, as it uses system specific IDs
        """
        data = None
        data_iter = BleCommunicationBleak.get_data([], bt_device)
        async for d in data_iter:
            if mac == d[0]:
                log.info("Data found")
                data = d[1]
                await data_iter.aclose()

        return data or ""

    async def get_history_data(
        self, mac: str, start_time: datetime | None = None, max_items: int | None = None
    ) -> AsyncGenerator[bytearray, None]:
        """
        Get history data from a RuuviTag using GATT connection.

        Args:
            mac (str): MAC address of the RuuviTag
            start_time (datetime, optional): Start time for history data. Time should be in UTC.
            max_items (int, optional): Maximum number of history entries to fetch

        Yields:
            bytearray: Raw history data entries

        Raises:
            RuntimeError: If connection fails or required services not found
        """
        client = None
        try:
            log.debug("Connecting to device %s", mac)
            client = await self._connect_gatt(mac)
            log.debug("Connected to device %s", mac)

            tx_char, rx_char = self._get_history_service_characteristics(client)

            data_queue: asyncio.Queue[bytearray | None] = asyncio.Queue()

            def notification_handler(_, data: bytearray):
                # Ignore heartbeat data that starts with 0x05
                if data and data[0] == 0x05:
                    log.debug("Ignoring heartbeat data")
                    return
                log.debug("Received data: %s", data)
                # Check for end-of-logs marker (0x3A 0x3A 0x10 0xFF ...)
                if len(data) >= 3 and all(b == 0xFF for b in data[3:]):
                    log.debug("Received end-of-logs marker")
                    data_queue.put_nowait(data)
                    data_queue.put_nowait(None)
                    return
                # Check for error message. Header is 0xF0 (0x30 30 F0 FF FF FF FF FF FF FF FF)
                if len(data) >= 11 and data[2] == 0xF0:
                    log.debug("Device reported error in log reading")
                    data_queue.put_nowait(data)
                    data_queue.put_nowait(None)
                    return
                data_queue.put_nowait(data)

            await client.start_notify(tx_char, notification_handler)

            command = self._create_send_history_command(start_time)

            log.debug("Sending command: %s", command)
            await client.write_gatt_char(rx_char, command)
            log.debug("Sent history command to device")

            items_received = 0
            while True:
                try:
                    data = await asyncio.wait_for(data_queue.get(), timeout=10.0)
                    if data is None:
                        break
                    yield data
                    items_received += 1
                    if max_items and items_received >= max_items:
                        break
                except asyncio.TimeoutError:
                    log.error("Timeout waiting for history data")
                    break

        except Exception as e:
            log.error("Failed to get history data from device %s: %r", mac, e)
            raise
        finally:
            if client:
                await client.disconnect()
                log.debug("Disconnected from device %s", mac)

    async def _connect_gatt(self, mac: str, max_retries: int = 3) -> BleakClient:
        # Connect to a BLE device using GATT.
        # NOTE: On macOS, the device address is not a MAC address, but a system specific ID
        client = BleakClient(mac)

        for attempt in range(max_retries):
            try:
                await client.connect()
                return client
            except Exception as e:  # noqa: PERF203
                if attempt == max_retries - 1:
                    raise
                log.debug("Connection attempt %s failed: %s - Retrying...", attempt + 1, str(e))
                await asyncio.sleep(1)

        return client  # Satisfy linter - this line will never be reached

    def _get_history_service_characteristics(
        self, client: BleakClient
    ) -> tuple[BleakGATTCharacteristic, BleakGATTCharacteristic]:
        # Get the history service
        # https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus
        history_service = next(
            (service for service in client.services if service.uuid.lower() == RUUVI_HISTORY_SERVICE_UUID.lower()),
            None,
        )
        if not history_service:
            raise RuntimeError("History service not found - device may not support history")

        tx_char = history_service.get_characteristic(RUUVI_HISTORY_TX_CHAR_UUID)
        rx_char = history_service.get_characteristic(RUUVI_HISTORY_RX_CHAR_UUID)

        if not tx_char or not rx_char:
            raise RuntimeError("Required characteristics not found")

        return tx_char, rx_char

    def _create_send_history_command(self, start_time: datetime | None = None):
        end_time = int(datetime.now(timezone.utc).timestamp())
        start_time_to_use = int(start_time.timestamp()) if start_time else 0

        command = bytearray(
            [
                0x3A,
                0x3A,
                0x11,  # Header for temperature query
                (end_time >> 24) & 0xFF,  # End timestamp byte 1 (most significant)
                (end_time >> 16) & 0xFF,  # End timestamp byte 2
                (end_time >> 8) & 0xFF,  # End timestamp byte 3
                end_time & 0xFF,  # End timestamp byte 4
                (start_time_to_use >> 24) & 0xFF,  # Start timestamp byte 1 (most significant)
                (start_time_to_use >> 16) & 0xFF,  # Start timestamp byte 2
                (start_time_to_use >> 8) & 0xFF,  # Start timestamp byte 3
                start_time_to_use & 0xFF,  # Start timestamp byte 4
            ]
        )

        return command
