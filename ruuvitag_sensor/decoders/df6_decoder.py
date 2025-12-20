from __future__ import annotations

import logging
import math
import struct

from ruuvitag_sensor.ruuvi_types import ByteData, SensorData6

log = logging.getLogger(__name__)


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
