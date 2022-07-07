from __future__ import division

import base64
import math
import logging
import struct

log = logging.getLogger(__name__)


def get_decoder(data_type):
    """
    Get correct decoder for Data Type.

    Returns:
        object: Data decoder
    """
    if data_type == 2:
        log.warning("DATA TYPE 2 IS OBSOLETE. UPDATE YOUR TAG")
        # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_04.md
        return UrlDecoder()
    if data_type == 4:
        log.warning("DATA TYPE 4 IS OBSOLETE. UPDATE YOUR TAG")
        # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_04.md
        return UrlDecoder()
    if data_type == 3:
        log.warning("DATA TYPE 3 IS DEPRECATED - UPDATE YOUR TAG")
        # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_03.md
        return Df3Decoder()
    return Df5Decoder()


def parse_mac(data_format, payload_mac):
    """
    Data format 5 payload contains MAC-address in format e.g. e62eb92e73e5

    Returns:
        string: MAC separated and in upper case e.g. E6:2E:B9:2E:73:E5
    """
    if data_format == 5:
        return ':'.join(payload_mac[i:i+2] for i in range(0, 12, 2)).upper()
    return payload_mac


class UrlDecoder(object):
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

    def _get_temperature(self, decoded):
        """Return temperature in celsius"""
        temp = (decoded[2] & 127) + decoded[3] / 100
        sign = (decoded[2] >> 7) & 1
        if sign == 0:
            return round(temp, 2)
        return round(-1 * temp, 2)

    def _get_humidity(self, decoded):
        """Return humidity %"""
        return decoded[1] * 0.5

    def _get_pressure(self, decoded):
        """Return air pressure hPa"""
        pressure = ((decoded[4] << 8) + decoded[5]) + 50000
        return pressure / 100

    def decode_data(self, encoded):
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
            decoded = bytearray(base64.b64decode(encoded, '-_'))
            return {
                'data_format': data_format,
                'temperature': self._get_temperature(decoded),
                'humidity': self._get_humidity(decoded),
                'pressure': self._get_pressure(decoded),
                'identifier': identifier
            }
        except Exception:
            log.exception('Encoded value: %s not valid', encoded)
            return None


class Df3Decoder(object):
    """
    Decodes data from RuuviTag with Data Format 3
    Protocol specification:
    https://github.com/ruuvi/ruuvi-sensor-protocols
    """

    def _get_temperature(self, data):
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

    def _get_humidity(self, data):
        """Return humidity %"""
        return data[1] * 0.5

    def _get_pressure(self, data):
        """Return air pressure hPa"""
        return (data[4] + 50000) / 100

    def _get_acceleration(self, data):
        """Return acceleration mG"""
        return data[5:8]

    def _get_battery(self, data):
        """Return battery mV"""
        return data[8]

    def decode_data(self, data):
        """
        Decode sensor data.

        Returns:
            dict: Sensor values
        """
        try:
            byte_data = struct.unpack('>BBbBHhhhH', bytearray.fromhex(data[:28]))
            acc_x, acc_y, acc_z = self._get_acceleration(byte_data)
            return {
                'data_format': 3,
                'humidity': self._get_humidity(byte_data),
                'temperature': self._get_temperature(byte_data),
                'pressure': self._get_pressure(byte_data),
                'acceleration': math.sqrt(
                    acc_x * acc_x + acc_y * acc_y + acc_z * acc_z),
                'acceleration_x': acc_x,
                'acceleration_y': acc_y,
                'acceleration_z': acc_z,
                'battery': self._get_battery(byte_data)
            }
        except Exception:
            log.exception('Value: %s not valid', data)
            return None


class Df5Decoder(object):
    """
    Decodes data from RuuviTag with Data Format 5
    Protocol specification:
    https://github.com/ruuvi/ruuvi-sensor-protocols
    """

    def _get_temperature(self, data):
        """Return temperature in celsius"""
        if data[1] == -32768:
            return None

        return round(data[1] / 200, 2)

    def _get_humidity(self, data):
        """Return humidity %"""
        if data[2] == 65535:
            return None

        return round(data[2] / 400, 2)

    def _get_pressure(self, data):
        """Return air pressure hPa"""
        if data[3] == 0xFFFF:
            return None

        return round((data[3] + 50000) / 100, 2)

    def _get_acceleration(self, data):
        """Return acceleration mG"""
        if (data[4] == -32768 or data[5] == -32768 or data[6] == -32768):
            return (None, None, None)

        return data[4:7]

    def _get_powerinfo(self, data):
        """Return battery voltage and tx power"""
        battery_voltage = data[7] >> 5
        tx_power = data[7] & 0x001F

        return (battery_voltage, tx_power)

    def _get_battery(self, data):
        """Return battery mV"""
        battery_voltage = self._get_powerinfo(data)[0]
        if battery_voltage == 0b11111111111:
            return None

        return battery_voltage + 1600

    def _get_txpower(self, data):
        """Return transmit power"""
        tx_power = self._get_powerinfo(data)[1]
        if tx_power == 0b11111:
            return None

        return -40 + (tx_power * 2)

    def _get_movementcounter(self, data):
        return data[8]

    def _get_measurementsequencenumber(self, data):
        return data[9]

    def _get_mac(self, data):
        return ''.join(f'{x:02x}' for x in data[10:])

    def decode_data(self, data):
        """
        Decode sensor data.

        Returns:
            dict: Sensor values
        """
        try:
            byte_data = struct.unpack('>BhHHhhhHBH6B', bytearray.fromhex(data[:48]))

            acc_x, acc_y, acc_z = self._get_acceleration(byte_data)
            return {
                'data_format': 5,
                'humidity': self._get_humidity(byte_data),
                'temperature': self._get_temperature(byte_data),
                'pressure': self._get_pressure(byte_data),
                'acceleration': math.sqrt(acc_x * acc_x + acc_y * acc_y + acc_z * acc_z),
                'acceleration_x': acc_x,
                'acceleration_y': acc_y,
                'acceleration_z': acc_z,
                'tx_power': self._get_txpower(byte_data),
                'battery': self._get_battery(byte_data),
                'movement_counter': self._get_movementcounter(byte_data),
                'measurement_sequence_number': self._get_measurementsequencenumber(byte_data),
                'mac': self._get_mac(byte_data)
            }
        except Exception:
            log.exception('Value: %s not valid', data)
            return None
