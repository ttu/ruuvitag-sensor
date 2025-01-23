import asyncio
import logging
import os
import re
import struct
import sys
from datetime import datetime
from typing import AsyncGenerator, List, Optional, Tuple

from bleak import BleakClient, BleakScanner
from bleak.backends.scanner import AdvertisementData, AdvertisementDataCallback, BLEDevice

from ruuvitag_sensor.adapters import BleCommunicationAsync
from ruuvitag_sensor.adapters.utils import rssi_to_hex
from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData

MAC_REGEX = "[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$"
RUUVI_HISTORY_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
RUUVI_HISTORY_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
RUUVI_HISTORY_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"


def _get_scanner(detection_callback: AdvertisementDataCallback, bt_device: str = ""):
    # NOTE: On Linux - bleak.exc.BleakError: passive scanning mode requires bluez or_patterns
    # NOTE: On macOS - bleak.exc.BleakError: macOS does not support passive scanning
    scanning_mode = "passive" if sys.platform.startswith("win") else "active"

    if "bleak_dev" in os.environ.get("RUUVI_BLE_ADAPTER", "").lower():
        from ruuvitag_sensor.adapters.development.dev_bleak_scanner import DevBleakScanner

        return DevBleakScanner(detection_callback, scanning_mode)

    if bt_device:
        return BleakScanner(
            detection_callback=detection_callback,
            scanning_mode=scanning_mode,  # type: ignore[arg-type]
            adapter=bt_device,
        )

    return BleakScanner(detection_callback=detection_callback, scanning_mode=scanning_mode)  # type: ignore[arg-type]


queue = asyncio.Queue[Tuple[str, str]]()

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
    async def get_data(blacklist: List[str] = [], bt_device: str = "") -> AsyncGenerator[MacAndRawData, None]:
        async def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            # On macOS device address is not a MAC address, but a system specific ID
            # https://github.com/hbldh/bleak/issues/140
            mac: str = device.address if re.match(MAC_REGEX, device.address.lower()) else ""
            if mac and mac in blacklist:
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
                next_item: Tuple[str, str] = await queue.get()
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
        self, mac: str, start_time: Optional[datetime] = None, max_items: Optional[int] = None
    ) -> List[dict]:
        """
        Get history data from a RuuviTag using GATT connection.

        Args:
            mac (str): MAC address of the RuuviTag
            start_time (datetime, optional): Start time for history data
            max_items (int, optional): Maximum number of history entries to fetch

        Returns:
            List[dict]: List of historical sensor readings

        Raises:
            RuntimeError: If connection fails or required services not found
        """
        history_data: List[bytearray] = []
        client = None

        try:
            # Connect to device
            client = await self._connect_gatt(mac)
            log.debug("Connected to device %s", mac)

            # Get the history service
            # https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus
            history_service = next(
                (service for service in client.services if service.uuid.lower() == RUUVI_HISTORY_SERVICE_UUID.lower()),
                None,
            )
            if not history_service:
                raise RuntimeError(f"History service not found - device {mac} may not support history")

            # Get characteristics
            tx_char = history_service.get_characteristic(RUUVI_HISTORY_TX_CHAR_UUID)
            rx_char = history_service.get_characteristic(RUUVI_HISTORY_RX_CHAR_UUID)

            if not tx_char or not rx_char:
                raise RuntimeError("Required characteristics not found")

            # Set up notification handler
            notification_received = asyncio.Event()

            def notification_handler(_, data: bytearray):
                history_data.append(data)
                notification_received.set()

            # Enable notifications
            await client.start_notify(tx_char, notification_handler)

            # Request history data
            command = bytearray([0x26])  # Get logged history command
            if start_time:
                timestamp = int(start_time.timestamp())
                command.extend(struct.pack("<I", timestamp))

            await client.write_gatt_char(rx_char, command)
            log.debug("Requested history data from device %s", mac)

            # Wait for initial notification
            await asyncio.wait_for(notification_received.wait(), timeout=10.0)

            # Wait for more data
            try:
                while True:
                    notification_received.clear()
                    await asyncio.wait_for(notification_received.wait(), timeout=5.0)
                    # Check if we've reached the maximum number of items
                    if max_items and len(history_data) >= max_items:
                        log.debug("Reached maximum number of items (%d)", max_items)
                        break
            except asyncio.TimeoutError:
                # No more data received for 1 second - assume transfer complete
                pass

            # Parse collected data
            parsed_data = []
            for data_point in history_data:
                if len(data_point) < 10:  # Minimum valid data length
                    continue

                timestamp = struct.unpack("<I", data_point[0:4])[0]
                measurement = self._parse_history_data(data_point[4:])
                if measurement:
                    measurement["timestamp"] = datetime.fromtimestamp(timestamp)
                    parsed_data.append(measurement)

            log.info("Downloaded %d history entries from device %s", len(parsed_data), mac)
            return parsed_data
        except Exception as e:
            log.error(f"Failed to get history data from device {mac}: {e}")
        finally:
            if client:
                await client.disconnect()
                log.debug("Disconnected from device %s", mac)
        return []

    async def _connect_gatt(self, mac: str) -> BleakClient:
        """
        Connect to a BLE device using GATT.

        NOTE: On macOS, the device address is not a MAC address, but a system specific ID

        Args:
            mac (str): MAC address of the device to connect to

        Returns:
            BleakClient: Connected BLE client
        """
        client = BleakClient(mac)
        # TODO: Implement retry logic. connect fails for some reason pretty often.
        await client.connect()
        return client

    def _parse_history_data(self, data: bytes) -> Optional[dict]:
        """
        Parse history data point from RuuviTag

        Args:
            data (bytes): Raw history data point

        Returns:
            Optional[dict]: Parsed sensor data or None if parsing fails
        """
        try:
            temperature = struct.unpack("<h", data[0:2])[0] * 0.005
            humidity = struct.unpack("<H", data[2:4])[0] * 0.0025
            pressure = struct.unpack("<H", data[4:6])[0] + 50000

            return {
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure,
                "data_format": 5,  # History data uses similar format to data format 5
            }
        except Exception as e:
            log.error(f"Failed to parse history data: {e}")
            return None
