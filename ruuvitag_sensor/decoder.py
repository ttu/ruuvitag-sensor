from __future__ import annotations

import base64
import logging
import math
import struct

from ruuvitag_sensor.ruuvi_types import (
    ByteData,
    SensorData3,
    SensorData5,
    SensorData6,
    SensorDataE1,
    SensorDataUrl,
    SensorHistoryData,
)

log = logging.getLogger(__name__)


def get_decoder(data_format: int | str) -> UrlDecoder | Df3Decoder | Df5Decoder | Df6Decoder | DfE1Decoder:
    """
    Get correct decoder for Data Format.

    Args:
        data_format: The data format number (2, 3, 4, 5, or 6)

    Returns:
        object: Data decoder instance

    Raises:
        ValueError: If data_format is not a recognized format
    """
    # Data formats are ordered by priority, so the most common formats are at the top.
    match data_format:
        case 5:
            # https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-5-rawv2
            return Df5Decoder()
        case 6:
            # https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-6
            return Df6Decoder()
        case "E1":
            # https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-e1.md
            return DfE1Decoder()
        case 2:
            log.warning("DATA TYPE 2 IS OBSOLETE. UPDATE YOUR TAG")
            # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_04.md
            return UrlDecoder()
        case 3:
            log.warning("DATA TYPE 3 IS DEPRECATED - UPDATE YOUR TAG")
            # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_03.md
            return Df3Decoder()
        case 4:
            log.warning("DATA TYPE 4 IS OBSOLETE. UPDATE YOUR TAG")
            # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_04.md
            return UrlDecoder()
        case _:
            # This should never happen in normal operation since DataFormats.convert_data()
            # already validates and identifies the data format. If we reach here, it indicates
            # a programming error (e.g., convert_data was bypassed or returned an unhandled format).
            raise ValueError(f"Unknown data format: {data_format}")


def parse_mac(data_format: int | str, payload_mac: str) -> str:
    """
    Data format 5 payload contains MAC-address in format e.g. e62eb92e73e5

    Returns:
        string: MAC separated and in upper case e.g. E6:2E:B9:2E:73:E5
    """
    match data_format:
        case 5:
            return ":".join(payload_mac[i : i + 2] for i in range(0, 12, 2)).upper()
        case _:
            return payload_mac


class UrlDecoder:
    """
    Decodes data from RuuviTag url
    Protocol specification:
    https://github.com/ruuvi/ruuvi-sensor-protocols

    Decoder operations are ported from:
    https://github.com/ruuvi/sensor-protocol-for-eddystone-url/blob/master/index.html

    0:   uint8_t     format;          // (0x02 = realtime sensor readings)
    1:   uint8_t     humidity;        // one lsb is 0.5%
    2-3: uint16_t    temperature;     // Signed 8.8 fixed-point notation.
    4-5: uint16_t    pressure;        // (-50kPa)
    6-7: uint16_t    time;            // seconds (now from reset)

    The bytes for temperature, pressure and time are swapped during the encoding
    """

    def _get_temperature(self, decoded: bytearray) -> float:
        """Return temperature in celsius"""
        temp = (decoded[2] & 127) + decoded[3] / 100
        sign = (decoded[2] >> 7) & 1
        if sign == 0:
            return round(temp, 2)
        return round(-1 * temp, 2)

    def _get_humidity(self, decoded: bytearray) -> float:
        """Return humidity %"""
        return decoded[1] * 0.5

    def _get_pressure(self, decoded: bytearray) -> float:
        """Return air pressure hPa"""
        pressure = ((decoded[4] << 8) + decoded[5]) + 50000
        return pressure / 100

    def decode_data(self, encoded) -> SensorDataUrl | None:
        """
        Decode sensor data.

        Returns:
            dict: Sensor values
        """
        try:
            identifier = None
            data_format = 2
            if len(encoded) > 8:
                data_format = 4
                identifier = encoded[8:]
                encoded = encoded[:8]
            decoded = bytearray(base64.b64decode(encoded, "-_"))  # type: ignore
            return {
                "data_format": data_format,
                "temperature": self._get_temperature(decoded),
                "humidity": self._get_humidity(decoded),
                "pressure": self._get_pressure(decoded),
                "identifier": identifier,
            }
        except Exception:
            log.exception("Encoded value: %s not valid", encoded)
            return None


class Df3Decoder:
    """
    Decodes data from RuuviTag with Data Format 3
    Protocol specification:
    https://github.com/ruuvi/ruuvi-sensor-protocols
    """

    def _get_temperature(self, data: ByteData) -> float:
        """Return temperature in celsius"""

        # The temperature is in two fields, one for the integer part,
        # one for the fraction
        #
        # The integer part was decoded as a signed two's complement number,
        # but this isn't how it's really stored. The MSB is a sign, the lower
        # 7 bits are the unsigned temperature value.
        #
        # To convert from the decoded value we have to add 128 and then negate,
        # if the decoded value was negative
        frac = data[3] / 100
        if data[2] < 0:
            return -(data[2] + 128 + frac)

        return data[2] + frac

    def _get_humidity(self, data: ByteData) -> float:
        """Return humidity %"""
        return data[1] * 0.5

    def _get_pressure(self, data: ByteData) -> float:
        """Return air pressure hPa"""
        return (data[4] + 50000) / 100

    def _get_acceleration(self, data: ByteData) -> tuple[int, int, int]:
        """Return acceleration mG"""
        return data[5:8]  # type: ignore

    def _get_battery(self, data: ByteData) -> int:
        """Return battery mV"""
        return data[8]

    def decode_data(self, data: str) -> SensorData3 | None:
        """
        Decode sensor data.

        Returns:
            dict: Sensor values
        """
        try:
            byte_data: ByteData = struct.unpack(">BBbBHhhhH", bytearray.fromhex(data[:28]))
            acc_x, acc_y, acc_z = self._get_acceleration(byte_data)
            return {
                "data_format": 3,
                "humidity": self._get_humidity(byte_data),
                "temperature": self._get_temperature(byte_data),
                "pressure": self._get_pressure(byte_data),
                "acceleration": math.sqrt(acc_x * acc_x + acc_y * acc_y + acc_z * acc_z),
                "acceleration_x": acc_x,
                "acceleration_y": acc_y,
                "acceleration_z": acc_z,
                "battery": self._get_battery(byte_data),
            }
        except Exception:
            log.exception("Value: %s not valid", data)
            return None


class Df5Decoder:
    """
    Decodes data from RuuviTag with Data Format 5
    Protocol specification:
    https://github.com/ruuvi/ruuvi-sensor-protocols
    """

    def _get_temperature(self, data: ByteData) -> float | None:
        """Return temperature in celsius"""
        if data[1] == -32768:
            return None

        return round(data[1] / 200, 2)

    def _get_humidity(self, data: ByteData) -> float | None:
        """Return humidity %"""
        if data[2] == 65535:
            return None

        return round(data[2] / 400, 2)

    def _get_pressure(self, data: ByteData) -> float | None:
        """Return air pressure hPa"""
        if data[3] == 0xFFFF:
            return None

        return round((data[3] + 50000) / 100, 2)

    def _get_acceleration(self, data: ByteData) -> tuple[None, None, None] | tuple[int, int, int]:
        """Return acceleration mG"""
        if data[4] == -32768 or data[5] == -32768 or data[6] == -32768:
            return (None, None, None)

        return data[4:7]  # type: ignore

    def _get_powerinfo(self, data: ByteData) -> tuple[int, int]:
        """Return battery voltage and tx power"""
        battery_voltage = data[7] >> 5
        tx_power = data[7] & 0x001F

        return (battery_voltage, tx_power)

    def _get_battery(self, data: ByteData) -> int | None:
        """Return battery mV"""
        battery_voltage = self._get_powerinfo(data)[0]
        if battery_voltage == 0b11111111111:
            return None

        return battery_voltage + 1600

    def _get_txpower(self, data: ByteData) -> int | None:
        """Return transmit power"""
        tx_power = self._get_powerinfo(data)[1]
        if tx_power == 0b11111:
            return None

        return -40 + (tx_power * 2)

    def _get_movementcounter(self, data: ByteData) -> int:
        return data[8]

    def _get_measurementsequencenumber(self, data: ByteData) -> int:
        return data[9]

    def _get_mac(self, data: ByteData):
        return "".join(f"{x:02x}" for x in data[10:])

    def _get_rssi(self, rssi_byte: str) -> int:
        """Return RSSI value in dBm."""
        rssi = int(rssi_byte, 16)
        if rssi > 127:
            rssi = (256 - rssi) * -1
        return rssi

    def decode_data(self, data: str) -> SensorData5 | None:
        """
        Decode sensor data.

        Returns:
            dict: Sensor values
        """
        try:
            byte_data: ByteData = struct.unpack(">BhHHhhhHBH6B", bytearray.fromhex(data[:48]))
            rssi = data[48:]

            acc_x, acc_y, acc_z = self._get_acceleration(byte_data)
            acc = math.sqrt(acc_x * acc_x + acc_y * acc_y + acc_z * acc_z) if acc_x and acc_y and acc_z else None

            # NOTE: Value parsing methods can return None, but it shouldn't happen with the
            # production firmware. Therefore properties are not optional on SensorData-type.

            return {
                "data_format": 5,
                "humidity": self._get_humidity(byte_data),  # type: ignore
                "temperature": self._get_temperature(byte_data),  # type: ignore
                "pressure": self._get_pressure(byte_data),  # type: ignore
                "acceleration": acc,  # type: ignore
                "acceleration_x": acc_x,  # type: ignore
                "acceleration_y": acc_y,  # type: ignore
                "acceleration_z": acc_z,  # type: ignore
                "tx_power": self._get_txpower(byte_data),  # type: ignore
                "battery": self._get_battery(byte_data),  # type: ignore
                "movement_counter": self._get_movementcounter(byte_data),
                "measurement_sequence_number": self._get_measurementsequencenumber(byte_data),
                "mac": self._get_mac(byte_data),
                "rssi": self._get_rssi(rssi) if rssi else None,
            }
        except Exception:
            log.exception("Value: %s not valid", data)
            return None


class DfE1Decoder:
    """
    Decodes data from Ruuvi Air with Data Format E1
    Protocol specification:
    https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-e1.md
    """

    def _get_temperature(self, data: ByteData) -> float | None:
        """Return temperature in celsius"""
        if data[1] == -32768:
            return None
        return round(int(data[1]) * 0.005, 3)

    def _get_humidity(self, data: ByteData) -> float | None:
        """Return humidity %"""
        if data[2] == 65535:
            return None
        return round(int(data[2]) * 0.0025, 3)

    def _get_pressure(self, data: ByteData) -> float | None:
        """Return air pressure hPa"""
        if data[3] == 0xFFFF:
            return None
        return round((int(data[3]) + 50000) / 100, 2)

    def _get_pm1_ug_m3(self, data: ByteData) -> float | None:
        """Return PM 1.0, ug/m^3"""
        if data[4] == 0xFFFF:
            return None
        return round(int(data[4]) * 0.1, 1)

    def _get_pm25_ug_m3(self, data: ByteData) -> float | None:
        """Return PM 2.5, ug/m^3"""
        if data[5] == 0xFFFF:
            return None
        return round(int(data[5]) * 0.1, 1)

    def _get_pm4_ug_m3(self, data: ByteData) -> float | None:
        """Return PM 4.0, ug/m^3"""
        if data[6] == 0xFFFF:
            return None
        return round(int(data[6]) * 0.1, 1)

    def _get_pm10_ug_m3(self, data: ByteData) -> float | None:
        """Return PM 10.0, ug/m^3"""
        if data[7] == 0xFFFF:
            return None
        return round(int(data[7]) * 0.1, 1)

    def _get_co2_ppm(self, data: ByteData) -> int | None:
        """Return CO2 ppm"""
        if data[8] == 0xFFFF:
            return None
        return int(data[8])

    def _get_voc_index(self, data: ByteData) -> int | None:
        """Return VOC index (unitless, 9-bit)"""
        # VOC: bits [8:1] are in data[6], bit [0] (LSB) is FLAGS bit 6
        # As per spec: "9 bit unsigned, least significant bit in Flags byte"
        voc_high_bits = data[9]  # bits [8:1]
        voc_lsb = (data[14] >> 6) & 0x01  # bit [0]
        voc = (voc_high_bits << 1) | voc_lsb

        if voc == 511:  # 0x1FF
            return None

        return voc

    def _get_nox_index(self, data: ByteData) -> int | None:
        """Return NOx index (unitless, 9-bit)"""
        # NOx: bits [8:1] are in data[7], bit [0] (LSB) is FLAGS bit 7
        # As per spec: "9 bit unsigned, least significant bit in Flags byte"
        nox_high_bits = data[10]  # bits [8:1]
        nox_lsb = (data[14] >> 7) & 0x01  # bit [0]
        nox = (nox_high_bits << 1) | nox_lsb

        if nox == 511:  # 0x1FF
            return None

        return nox

    def _get_luminosity_lux(self, data: ByteData) -> float | None:
        """Return Luminosity Lux"""
        lumi_bytes = bytes(data[11])
        if lumi_bytes == b"\xff\xff\xff":
            return None
        lumi_val = int.from_bytes(lumi_bytes, byteorder="big")
        return round(lumi_val * 0.01, 2)

    def _get_measurementsequencenumber(self, data: ByteData) -> int | None:
        seq_bytes = bytes(data[13])
        if seq_bytes == b"\xff\xff\xff":
            return None
        return int.from_bytes(seq_bytes, byteorder="big")

    def _get_calibration_in_progress(self, data: ByteData) -> bool:
        # Bit 0 of flags indicates calibration status
        return bool(data[14] & 1)

    def _get_mac(self, data: ByteData) -> str:
        return ":".join(f"{b:02X}" for b in bytes(data[16]))

    def decode_data(self, data: str) -> SensorDataE1 | None:
        """
        Decode sensor data.

        Returns:
            dict: Sensor values
        """
        try:
            byte_data: ByteData = struct.unpack(">BhHHHHHHHBB3s3s3sB5s6s", bytearray.fromhex(data[:80]))
            return {
                "data_format": "E1",
                "humidity": self._get_humidity(byte_data),  # type: ignore
                "temperature": self._get_temperature(byte_data),  # type: ignore
                "pressure": self._get_pressure(byte_data),  # type: ignore
                "pm_1": self._get_pm1_ug_m3(byte_data),  # type: ignore
                "pm_2_5": self._get_pm25_ug_m3(byte_data),  # type: ignore
                "pm_4": self._get_pm4_ug_m3(byte_data),  # type: ignore
                "pm_10": self._get_pm10_ug_m3(byte_data),  # type: ignore
                "co2": self._get_co2_ppm(byte_data),  # type: ignore
                "voc": self._get_voc_index(byte_data),  # type: ignore
                "nox": self._get_nox_index(byte_data),  # type: ignore
                "luminosity": self._get_luminosity_lux(byte_data),  # type: ignore
                "measurement_sequence_number": self._get_measurementsequencenumber(byte_data),  # type: ignore
                "calibration_in_progress": self._get_calibration_in_progress(byte_data),
                "mac": self._get_mac(byte_data),
            }
        except Exception:
            log.exception("Value: %s not valid", data)
            return None


class Df6Decoder:
    """
    Decodes data from Ruuvi Air with Data Format 6
    Protocol specification:
    https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-6

    Data Format 6 is used by Ruuvi Air for air quality monitoring.
    It includes CO2, PM2.5, VOC, NOx, luminosity along with traditional sensors.
    """

    def _get_temperature(self, data: ByteData) -> float | None:
        """Return temperature in celsius"""
        if data[1] == -32768:
            return None

        return round(data[1] * 0.005, 3)

    def _get_humidity(self, data: ByteData) -> float | None:
        """Return humidity %"""
        if data[2] == 65535:
            return None

        return round(data[2] * 0.0025, 3)

    def _get_pressure(self, data: ByteData) -> float | None:
        """Return air pressure hPa"""
        if data[3] == 65535:
            return None

        return round((data[3] + 50000) / 100, 2)

    def _get_pm_2_5(self, data: ByteData) -> float | None:
        """Return PM 2.5 in ug/m³"""
        if data[4] == 65535:
            return None

        return round(data[4] * 0.1, 1)

    def _get_co2(self, data: ByteData) -> int | None:
        """Return CO2 concentration in ppm"""
        if data[5] == 65535:
            return None

        return data[5]

    def _get_voc(self, data: ByteData) -> int | None:
        """Return VOC index (unitless, 9-bit)"""
        # VOC: bits [8:1] are in data[6], bit [0] (LSB) is FLAGS bit 6
        # As per spec: "9 bit unsigned, least significant bit in Flags byte"
        voc_high_bits = data[6]  # bits [8:1]
        voc_lsb = (data[11] >> 6) & 0x01  # bit [0]
        voc = (voc_high_bits << 1) | voc_lsb

        if voc == 511:  # 0x1FF
            return None

        return voc

    def _get_nox(self, data: ByteData) -> int | None:
        """Return NOx index (unitless, 9-bit)"""
        # NOx: bits [8:1] are in data[7], bit [0] (LSB) is FLAGS bit 7
        # As per spec: "9 bit unsigned, least significant bit in Flags byte"
        nox_high_bits = data[7]  # bits [8:1]
        nox_lsb = (data[11] >> 7) & 0x01  # bit [0]
        nox = (nox_high_bits << 1) | nox_lsb

        if nox == 511:  # 0x1FF
            return None

        return nox

    def _get_luminosity(self, data: ByteData) -> float | None:
        """Return luminosity in lux (logarithmic scale)"""
        code = data[8]

        if code == 255:
            return None

        if code == 0:
            return 0.0

        # Decode logarithmic value
        MAX_VALUE = 65535
        MAX_CODE = 254
        DELTA = math.log(MAX_VALUE + 1) / MAX_CODE
        value = math.exp(code * DELTA) - 1

        return round(value, 2)

    def _get_measurement_sequence_number(self, data: ByteData) -> int:
        """Return measurement sequence number"""
        return data[10]

    def _get_calibration_in_progress(self, data: ByteData) -> bool:
        """Return calibration status from flags byte"""
        # Bit 0 of flags byte indicates calibration status
        return bool(data[11] & 0x01)

    def _get_mac(self, data: ByteData) -> str:
        """Return MAC address (last 3 bytes)"""
        return "".join(f"{x:02x}" for x in data[12:15])

    def decode_data(self, data: str) -> SensorData6 | None:
        """
        Decode sensor data.

        Returns:
            dict: Sensor values
        """
        try:
            # Data Format 6 structure (20 bytes):
            # 0: data_format (uint8)
            # 1-2: temperature (int16)
            # 3-4: humidity (uint16)
            # 5-6: pressure (uint16)
            # 7-8: pm_2_5 (uint16)
            # 9-10: co2 (uint16)
            # 11: voc_low (uint8)
            # 12: nox_low (uint8)
            # 13: luminosity (uint8)
            # 14: reserved (uint8)
            # 15: measurement_sequence (uint8)
            # 16: flags (uint8)
            # 17-19: mac (3 bytes)
            byte_data: ByteData = struct.unpack(">BhHHHHBBBBBBBBB", bytearray.fromhex(data[:40]))

            return {
                "data_format": 6,
                "temperature": self._get_temperature(byte_data),  # type: ignore
                "humidity": self._get_humidity(byte_data),  # type: ignore
                "pressure": self._get_pressure(byte_data),  # type: ignore
                "pm_2_5": self._get_pm_2_5(byte_data),  # type: ignore
                "co2": self._get_co2(byte_data),  # type: ignore
                "voc": self._get_voc(byte_data),  # type: ignore
                "nox": self._get_nox(byte_data),  # type: ignore
                "luminosity": self._get_luminosity(byte_data),  # type: ignore
                "measurement_sequence_number": self._get_measurement_sequence_number(byte_data),
                "calibration_in_progress": self._get_calibration_in_progress(byte_data),
                "mac": self._get_mac(byte_data),
            }
        except Exception:
            log.exception("Value: %s not valid", data)
            return None


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
    - Next 2 bytes: Sensor data (uint16, little-endian)
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
        # Check for command byte 0x3A, type 0x3A, and remaining bytes are 0xFF
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
        # Temperature is in 0.01°C units, little-endian
        temp_bytes = bytes.fromhex("".join(data[9:11]))
        temp_raw = int.from_bytes(temp_bytes, "big")
        return round(temp_raw * 0.01, 2)

    def _get_humidity(self, data: list[str]) -> float | None:
        """Return humidity %"""
        if data[1] != "31":  # '1' for humidity
            return None
        # Humidity is in 0.01% units, little-endian
        humidity_bytes = bytes.fromhex("".join(data[9:11]))
        humidity_raw = int.from_bytes(humidity_bytes, "big")
        return round(humidity_raw * 0.01, 2)

    def _get_pressure(self, data: list[str]) -> float | None:
        """Return air pressure hPa"""
        if data[1] != "32":  # '2' for pressure
            return None
        # Pressure is in hPa units, little-endian
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
                log.info("History data too short: %d bytes", len(hex_values))
                return None

            # Verify this is a history log entry
            if hex_values[0] != "3a":  # ':'
                log.info("Invalid command byte: %d", data[0])
                return None

            # Check for error header
            if self._is_error_packet(hex_values):
                log.info("Device reported error in log reading")
                return None

            # Check for end marker packet
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
                    log.info("Invalid packet type: %d - %s", packet_type, data)
                    return None

        except Exception:
            log.exception("Value not valid: %s", data)
            return None
