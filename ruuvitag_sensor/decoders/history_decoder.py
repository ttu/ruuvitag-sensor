from __future__ import annotations

import logging

from ruuvitag_sensor.ruuvi_types import SensorHistoryData

log = logging.getLogger(__name__)


class HistoryDecoder:
    """
    Decodes history data from RuuviTag
    Protocol specification:
    https://github.com/ruuvi/docs/blob/master/communication/bluetooth-connection/nordic-uart-service-nus/log-read.md

    Data format:
    - First byte: Command byte (0x3A)
    - Second byte: Packet type (0x30 = temperature, 0x31 = humidity, 0x32 = pressure)
    - Third byte: Header byte (skipped or error)
    - Next 4 bytes: Clock time (seconds since unix epoch)
    - Next 2 bytes: Reserved (always 0x00)
    - Next 2 bytes: Sensor data (uint16, big-endian)
        Temperature: 0.01°C units
        Humidity: 0.01% units
        Pressure: Raw value in hPa

    Special case:
    - End marker packet has command byte 0x3A followed by 0x3A
    """

    def _is_error_packet(self, data: list[str]) -> bool:
        """Check if this is an error packet"""
        return data[2] == "F0" and all(b == "ff" for b in data[3:])

    def _is_end_marker(self, data: list[str]) -> bool:
        """Check if this is an end marker packet"""
        return data[0] == "3a" and data[1] == "3a" and all(b == "ff" for b in data[3:])

    def _get_timestamp(self, data: list[str]) -> int:
        """Return timestamp"""
        # The timestamp is a 4-byte value after the header byte, in seconds since Unix epoch
        timestamp_bytes = bytes.fromhex("".join(data[3:7]))
        timestamp = int.from_bytes(timestamp_bytes, "big")
        return timestamp
        # return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    def _get_temperature(self, data: list[str]) -> float | None:
        """Return temperature in celsius"""
        if data[1] != "30":  # '0' for temperature
            return None
        # Temperature is in 0.01°C units, big-endian
        temp_bytes = bytes.fromhex("".join(data[9:11]))
        temp_raw = int.from_bytes(temp_bytes, "big")
        return round(temp_raw * 0.01, 2)

    def _get_humidity(self, data: list[str]) -> float | None:
        """Return humidity %"""
        if data[1] != "31":  # '1' for humidity
            return None
        # Humidity is in 0.01% units, big-endian
        humidity_bytes = bytes.fromhex("".join(data[9:11]))
        humidity_raw = int.from_bytes(humidity_bytes, "big")
        return round(humidity_raw * 0.01, 2)

    def _get_pressure(self, data: list[str]) -> float | None:
        """Return air pressure hPa"""
        if data[1] != "32":  # '2' for pressure
            return None
        # Pressure is in hPa units, big-endian
        pressure_bytes = bytes.fromhex("".join(data[9:11]))
        pressure_raw = int.from_bytes(pressure_bytes, "big")
        return float(pressure_raw)

    def decode_data(self, data: bytearray) -> SensorHistoryData | None:  # noqa: PLR0911
        """
        Decode history data from RuuviTag.

        The data format follows the NUS log format.

        Args:
            data: Raw history data bytearray

        Returns:
            SensorDataHistory: Decoded sensor values with timestamp, or None if decoding fails
            Returns None for both invalid data and end marker packets
        """
        try:
            hex_values = [format(x, "02x") for x in data]

            if len(hex_values) != 11:
                if len(data) >= 5 and (data[0] == 0x3B or data[0] == 0xE1 or (len(data) >= 38 and data[4] == 0xE1)):
                    log.error(
                        "Received data appears to be from Ruuvi Air device. "
                        "Please use device_type='ruuvi_air' when calling get_history_async() or download_history()"
                    )
                else:
                    log.info("History data unexpected length: %d bytes (expected 11)", len(hex_values))
                return None

            if hex_values[0] != "3a":
                log.info("Invalid command byte: 0x%02X (expected 0x3A)", data[0])
                return None

            if self._is_error_packet(hex_values):
                log.info("Device reported error in log reading")
                return None

            if self._is_end_marker(hex_values):
                log.debug("End marker packet received")
                return None

            # Each packet type contains one measurement
            packet_type = hex_values[1]
            match packet_type:
                case "30":  # '0' temperature
                    return {
                        "temperature": self._get_temperature(hex_values),
                        "humidity": None,
                        "pressure": None,
                        "timestamp": self._get_timestamp(hex_values),
                    }
                case "31":  # '1' humidity
                    return {
                        "temperature": None,
                        "humidity": self._get_humidity(hex_values),
                        "pressure": None,
                        "timestamp": self._get_timestamp(hex_values),
                    }
                case "32":  # '2' pressure
                    return {
                        "temperature": None,
                        "humidity": None,
                        "pressure": self._get_pressure(hex_values),
                        "timestamp": self._get_timestamp(hex_values),
                    }
                case _:
                    log.info("Invalid packet type: %s - %s", packet_type, data)
                    return None

        except Exception:
            log.exception("Value not valid: %s", data)
            return None
