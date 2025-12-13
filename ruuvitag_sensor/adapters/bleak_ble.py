import asyncio
import logging
import os
import re
import sys
from collections.abc import AsyncGenerator, Callable
from datetime import datetime, timezone
from enum import Enum

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


class HistoryNotificationAction(str, Enum):
    """Action types for history notification processing."""

    IGNORE = "ignore"  # Heartbeat data, should be ignored
    END = "end"  # End marker received
    ERROR = "error"  # Error packet received
    DATA = "data"  # Normal history data


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
        self,
        mac: str,
        start_time: datetime | None = None,
        max_items: int | None = None,
        device_type: str = "ruuvitag",
    ) -> AsyncGenerator[bytearray, None]:
        """
        Get history data from a RuuviTag or Ruuvi Air using GATT connection.

        Args:
            mac (str): MAC address or UUID of the device
            start_time (datetime, optional): Start time for history data. Time should be in UTC.
            max_items (int, optional): Maximum number of history entries to fetch
            device_type (str): Device type - "ruuvi_air" for Ruuvi Air,
                "ruuvitag" for RuuviTag (default: "ruuvitag")

        Yields:
            bytearray: Raw history data entries (packets for Ruuvi Air, single records for RuuviTag)

        Raises:
            RuntimeError: If connection fails or required services not found
        """
        client = None
        try:
            log.debug("Connecting to device %s", mac)
            client = await self._connect_gatt(mac)
            log.debug("Connected to device %s", mac)

            is_ruuvi_air = device_type == "ruuvi_air"

            # Try to negotiate larger MTU for Ruuvi Air (recommended: 247+ bytes)
            if is_ruuvi_air:
                await self._try_set_ruuvi_air_mtu(client)

            tx_char, rx_char = self._get_history_service_characteristics(client)

            data_queue: asyncio.Queue[bytearray | None] = asyncio.Queue()
            # Buffer for assembling split Ruuvi Air packets
            packet_buffer = bytearray()
            notification_handler = self._create_history_notification_handler(is_ruuvi_air, packet_buffer, data_queue)
            await client.start_notify(tx_char, notification_handler)

            command = self._create_send_history_command(start_time, use_air_format=is_ruuvi_air)

            log.debug("Sending command: %s", command.hex())
            await client.write_gatt_char(rx_char, command)
            log.debug("Sent history command to device")

            async for packet in self._iter_history_queue(data_queue, max_items=max_items):
                yield packet

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

    async def _try_set_ruuvi_air_mtu(self, client: BleakClient, mtu: int = 247) -> None:
        """Best-effort MTU negotiation for Ruuvi Air history transfers."""
        try:
            if hasattr(client, "set_mtu"):
                await client.set_mtu(mtu)  # type: ignore[attr-defined]
                log.debug("MTU set to %d", mtu)
        except Exception as e:
            log.debug("Could not set MTU: %s (continuing with default)", e)

    def _create_history_notification_handler(
        self,
        is_ruuvi_air: bool,
        packet_buffer: bytearray,
        queue: asyncio.Queue[bytearray | None],
    ) -> Callable[[BleakGATTCharacteristic, bytearray], None]:
        if is_ruuvi_air:
            return self._create_ruuvi_air_history_notification_handler(packet_buffer, queue)
        return self._create_ruuvitag_history_notification_handler(queue)

    def _create_ruuvi_air_history_notification_handler(
        self, packet_buffer: bytearray, queue: asyncio.Queue[bytearray | None]
    ) -> Callable[[BleakGATTCharacteristic, bytearray], None]:
        def handler(_, data: bytearray) -> None:
            if data and data[0] == 0x05:
                log.debug("Ignoring heartbeat data")
                return

            packet_buffer.extend(data)
            for packet in self._extract_ruuvi_air_history_packets(packet_buffer):
                action, processed_data = self._process_history_notification(packet, True)
                if self._enqueue_history_notification(action, processed_data, queue):
                    packet_buffer.clear()
                    break

        return handler

    def _create_ruuvitag_history_notification_handler(
        self, queue: asyncio.Queue[bytearray | None]
    ) -> Callable[[BleakGATTCharacteristic, bytearray], None]:
        def handler(_, data: bytearray) -> None:
            if data and data[0] == 0x05:
                log.debug("Ignoring heartbeat data")
                return

            action, processed_data = self._process_history_notification(data, False)
            if action == HistoryNotificationAction.IGNORE:
                return

            log.debug("Received data: %s", processed_data)
            self._enqueue_history_notification(action, processed_data, queue)

        return handler

    async def _iter_history_queue(
        self,
        queue: asyncio.Queue[bytearray | None],
        *,
        max_items: int | None,
        timeout_sec: float = 10.0,
    ) -> AsyncGenerator[bytearray, None]:
        items_received = 0
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=timeout_sec)
            except asyncio.TimeoutError:
                log.error("Timeout waiting for history data")
                return

            if data is None:
                return

            yield data
            items_received += 1
            if max_items and items_received >= max_items:
                return

    @staticmethod
    def _enqueue_history_notification(
        action: HistoryNotificationAction,
        processed_data: bytearray | None,
        queue: asyncio.Queue[bytearray | None],
    ) -> bool:
        """Enqueue processed history data and signal end/error with a None sentinel."""
        if action == HistoryNotificationAction.IGNORE:
            return False
        queue.put_nowait(processed_data)
        if action in (HistoryNotificationAction.END, HistoryNotificationAction.ERROR):
            queue.put_nowait(None)
            return True
        return False

    @staticmethod
    def _extract_ruuvi_air_history_packets(buffer: bytearray) -> list[bytearray]:
        """
        Extract complete Ruuvi Air history packets from a buffer.

        Ruuvi Air multi-record response packet framing (log write, multi-record):
          0..2: 0x3B 0x3B 0x20
          3:    num_records
          4:    record_length (expected 38 bytes)
          5..:  records (num_records * record_length)

        Packets may arrive split across BLE notifications, so we accumulate into a buffer and slice
        out complete frames when enough bytes are present.
        """
        header = b"\x3b\x3b\x20"
        packets: list[bytearray] = []

        while True:
            pos = buffer.find(header)
            if pos == -1:
                # Keep last 2 bytes in case header spans notifications.
                if len(buffer) > 2:
                    del buffer[:-2]
                return packets
            if pos > 0:
                del buffer[:pos]

            if len(buffer) < 5:
                return packets

            num_records = buffer[3]
            record_length = buffer[4]
            if record_length == 0:
                # Invalid; drop one byte and attempt to resync.
                del buffer[0]
                continue

            expected_size = 5 + (num_records * record_length)
            if len(buffer) < expected_size:
                return packets

            packets.append(bytearray(buffer[:expected_size]))
            del buffer[:expected_size]

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

    def _create_send_history_command(self, start_time: datetime | None = None, use_air_format: bool = False):
        """
        Create the 11-byte log read command.

        Args:
            start_time: Start time for history data. If None, uses 0 (all data).
            try_air_format: If True, use Ruuvi Air format (0x3B 0x3B 0x21),
                           otherwise use RuuviTag format (0x3A 0x3A 0x11).

        Returns:
            bytearray: 11-byte command
        """
        end_time = int(datetime.now(timezone.utc).timestamp())
        start_time_to_use = int(start_time.timestamp()) if start_time else 0

        if use_air_format:
            # Ruuvi Air format: 0x3B 0x3B 0x21 (multi-record read)
            dest = 0x3B
            src = 0x3B
            op = 0x21
        else:
            # RuuviTag format: 0x3A 0x3A 0x11 (single-record read)
            dest = 0x3A
            src = 0x3A
            op = 0x11

        command = bytearray(
            [
                dest,
                src,
                op,
                (end_time >> 24) & 0xFF,  # Current time byte 1 (most significant)
                (end_time >> 16) & 0xFF,  # Current time byte 2
                (end_time >> 8) & 0xFF,  # Current time byte 3
                end_time & 0xFF,  # Current time byte 4
                (start_time_to_use >> 24) & 0xFF,  # Start time byte 1 (most significant)
                (start_time_to_use >> 16) & 0xFF,  # Start time byte 2
                (start_time_to_use >> 8) & 0xFF,  # Start time byte 3
                start_time_to_use & 0xFF,  # Start time byte 4
            ]
        )

        return command

    @staticmethod
    def _process_history_notification(
        data: bytearray, is_ruuvi_air: bool = False
    ) -> tuple[HistoryNotificationAction, bytearray | None]:
        """
        Process history notification data and determine the action to take.

        Args:
            data: Raw notification data from BLE characteristic
            is_ruuvi_air: True if device is Ruuvi Air, False for RuuviTag

        Returns:
            Tuple of (action_type, data):
            - action_type: One of HistoryNotificationAction constants
            - data: The processed data (or None if action is IGNORE)

        Reference:
        - RuuviTag: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        - Ruuvi Air: https://github.com/ruuvi/docs/blob/8161abb9a08840fceb409aab69d6a7c12d3d5511/communication/bluetooth-connection/nordic-uart-service-nus/read-logged-history-ruuvi-air.md
        """
        action = HistoryNotificationAction.DATA
        processed: bytearray | None = data

        # Ignore heartbeat data that starts with 0x05
        if data and data[0] == 0x05:
            log.debug("Ignoring heartbeat data")
            action = HistoryNotificationAction.IGNORE
            processed = None
        elif is_ruuvi_air:
            # Ruuvi Air protocol
            if len(data) < 5:
                log.debug("Packet too short: %d bytes", len(data))
                action = HistoryNotificationAction.IGNORE
                processed = None
            # Verify packet header (destination=0x3B, source=0x3B, operation=0x20)
            elif data[0] != 0x3B or data[1] != 0x3B or data[2] != 0x20:
                log.debug("Invalid Ruuvi Air packet header: 0x%02X 0x%02X 0x%02X", data[0], data[1], data[2])
                action = HistoryNotificationAction.IGNORE
                processed = None
            # Check for end marker: num_records = 0
            elif data[3] == 0x00:
                log.debug("Received end-of-logs marker (Ruuvi Air)")
                action = HistoryNotificationAction.END
        # RuuviTag protocol
        # Check for error message first (before end marker check)
        # From docs: Error message has header type 0xF0 with payload 0xFF
        # Example: 0x30 30 F0 FF FF FF FF FF FF FF FF
        elif len(data) >= 11 and data[2] == 0xF0:
            log.debug("Device reported error in log reading")
            action = HistoryNotificationAction.ERROR
        # Check for end-of-logs marker (0x3A 0x3A 0x10 0xFF ...)
        # From docs: End marker is 0x3A 3A 10 0xFFFFFFFF FFFFFFFF (all 0xFF)
        # Must check that first 3 bytes match the pattern and rest are 0xFF
        elif (
            len(data) >= 3
            and data[0] == 0x3A
            and data[1] == 0x3A
            and data[2] == 0x10
            and all(b == 0xFF for b in data[3:])
        ):
            log.debug("Received end-of-logs marker (RuuviTag)")
            action = HistoryNotificationAction.END

        return action, processed
