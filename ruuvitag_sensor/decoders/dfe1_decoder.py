from __future__ import annotations

import logging
import struct

from ruuvitag_sensor.ruuvi_types import ByteData, SensorDataE1

log = logging.getLogger(__name__)


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
