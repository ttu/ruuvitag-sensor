from __future__ import annotations

import logging
import math
import struct

from ruuvitag_sensor.ruuvi_types import ByteData, SensorData5

log = logging.getLogger(__name__)


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
