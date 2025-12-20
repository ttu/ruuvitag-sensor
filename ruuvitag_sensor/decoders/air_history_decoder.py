from __future__ import annotations

import logging

from ruuvitag_sensor.ruuvi_types import SensorAirHistoryData

log = logging.getLogger(__name__)


class AirHistoryDecoder:
    """
    Decodes history data from Ruuvi Air
    Protocol specification:
    https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read-air.md

    Multi-record response packet format:
    - Byte 0: Destination (source index from request)
    - Byte 1: Source (0x3B = Air Quality endpoint)
    - Byte 2: Operation (0x20 = Multi-record log write)
    - Byte 3: Num records (number of records in this packet)
    - Byte 4: Record length (38 bytes)
    - Bytes 5+: Packed record data

    Each record (38 bytes):
    - Bytes 0-3: Timestamp (uint32_t BE, Unix timestamp in seconds)
    - Byte 4: Data format (0xE1)
    - Bytes 5-6: Temperature (int16_t BE, x 200)
    - Bytes 7-8: Humidity (uint16_t BE, x 400)
    - Bytes 9-10: Pressure (uint16_t BE, (Pressure - 50000) Pa)
    - Bytes 11-12: PM1.0 (uint16_t BE, x 10)
    - Bytes 13-14: PM2.5 (uint16_t BE, x 10)
    - Bytes 15-16: PM4.0 (uint16_t BE, x 10)
    - Bytes 17-18: PM10.0 (uint16_t BE, x 10)
    - Bytes 19-20: CO₂ (uint16_t BE, ppm)
    - Byte 21: VOC (uint8_t, bit 9 in flags)
    - Byte 22: NOx (uint8_t, bit 9 in flags)
    - Bytes 23-28: Reserved
    - Bytes 29-31: Sequence counter (uint24_t BE)
    - Byte 32: Flags (extended bits for 9-bit values)
    - Bytes 33-37: Reserved
    """

    def _is_end_marker(self, data: bytearray) -> bool:
        """Check if this is an end marker packet (num_records = 0)."""
        if len(data) < 5:
            return False
        # End marker: destination=0x3B, source=0x3B, operation=0x20, num_records=0, record_length=38
        return data[0] == 0x3B and data[1] == 0x3B and data[2] == 0x20 and data[3] == 0x00 and data[4] == 0x26

    def _get_timestamp(self, record_data: bytearray) -> int:
        """Extract timestamp from record (bytes 0-3, big-endian)."""
        return int.from_bytes(record_data[0:4], byteorder="big")

    def _get_temperature(self, record_data: bytearray) -> float | None:
        """Extract temperature from record (bytes 5-6, int16_t BE, x 200)."""
        temp_raw = int.from_bytes(record_data[5:7], byteorder="big", signed=False)
        if temp_raw == 0x8000:
            return None
        if temp_raw >= 0x8000:
            temp_raw = temp_raw - 0x10000
        return round(temp_raw / 200.0, 2)

    def _get_humidity(self, record_data: bytearray) -> float | None:
        """Extract humidity from record (bytes 7-8, uint16_t BE, x 400)."""
        humidity_raw = int.from_bytes(record_data[7:9], byteorder="big")
        return None if humidity_raw == 0xFFFF else round(humidity_raw / 400.0, 3)

    def _get_pressure(self, record_data: bytearray) -> float | None:
        """Extract pressure from record (bytes 9-10, uint16_t BE)."""
        pressure_raw = int.from_bytes(record_data[9:11], byteorder="big")
        return None if pressure_raw == 0xFFFF else round((pressure_raw + 50000) / 100.0, 2)

    def _get_pm_value(self, record_data: bytearray, offset: int) -> float | None:
        """Extract PM value from record (uint16_t BE, x 10)."""
        pm_raw = int.from_bytes(record_data[offset : offset + 2], byteorder="big")
        return None if pm_raw == 0xFFFF else round(pm_raw / 10.0, 1)

    def _get_co2(self, record_data: bytearray) -> int | None:
        """Extract CO2 from record (bytes 19-20, uint16_t BE)."""
        co2_raw = int.from_bytes(record_data[19:21], byteorder="big")
        return None if co2_raw == 0xFFFF else co2_raw

    def _get_9bit_value(self, record_data: bytearray, byte_offset: int, flag_bit: int) -> int | None:
        """Extract 9-bit value from record (8 bits in byte + 1 bit in flags)."""
        flags = record_data[32] if len(record_data) > 32 else 0
        value_byte = record_data[byte_offset]
        value_bit9 = (flags >> flag_bit) & 0x01
        value = value_byte | (value_bit9 << 8)
        return None if value == 0x1FF else value

    def _get_sequence(self, record_data: bytearray) -> int | None:
        """Extract sequence counter from record (bytes 29-31, uint24_t BE)."""
        seq_raw = int.from_bytes(record_data[29:32], byteorder="big")
        return None if seq_raw == 0xFFFFFF else seq_raw

    def _decode_record(self, record_data: bytearray) -> SensorAirHistoryData | None:
        """
        Decode a single 38-byte record.

        Args:
            record_data: 38-byte record data

        Returns:
            SensorAirHistoryData or None if invalid
        """
        if len(record_data) < 38:
            log.debug("Record too short: %d bytes", len(record_data))
            return None

        try:
            if record_data[4] != 0xE1:
                log.debug("Invalid data format: 0x%02X (expected 0xE1)", record_data[4])
                return None

            return {
                "timestamp": self._get_timestamp(record_data),
                "temperature": self._get_temperature(record_data),
                "humidity": self._get_humidity(record_data),
                "pressure": self._get_pressure(record_data),
                "pm_1": self._get_pm_value(record_data, 11),
                "pm_2_5": self._get_pm_value(record_data, 13),
                "pm_4": self._get_pm_value(record_data, 15),
                "pm_10": self._get_pm_value(record_data, 17),
                "co2": self._get_co2(record_data),
                "voc": self._get_9bit_value(record_data, 21, 6),
                "nox": self._get_9bit_value(record_data, 22, 7),
                "measurement_sequence_number": self._get_sequence(record_data),
            }

        except Exception:
            log.exception("Failed to decode record")
            return None

    def decode_data(self, data: bytearray) -> list[SensorAirHistoryData]:
        """
        Decode a multi-record response packet.

        Args:
            data: Raw packet data from BLE notification

        Returns:
            List of decoded records (empty list if end marker or invalid packet)
        """
        if len(data) < 5:
            log.debug("Packet too short: %d bytes", len(data))
            return []

        if self._is_end_marker(data):
            log.debug("End marker received")
            return []

        if data[0] != 0x3B or data[1] != 0x3B or data[2] != 0x20:
            log.debug("Invalid packet header: 0x%02X 0x%02X 0x%02X", data[0], data[1], data[2])
            return []

        num_records = data[3]
        record_length = data[4]

        if record_length != 38:
            log.debug("Unexpected record length: %d (expected 38)", record_length)
            return []

        if num_records == 0:
            log.debug("No records in packet")
            return []

        records = []
        header_size = 5
        for i in range(num_records):
            record_start = header_size + (i * record_length)
            record_end = record_start + record_length
            if record_end > len(data):
                log.debug("Not enough data for record %d", i)
                break
            record_data = data[record_start:record_end]
            if decoded := self._decode_record(record_data):
                records.append(decoded)

        return records
