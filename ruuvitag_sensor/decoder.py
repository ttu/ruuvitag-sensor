from __future__ import division

import base64
import math
import logging

log = logging.getLogger(__name__)


def get_decoder(data_type):
    '''
    Get correct decoder for Data Type.

    Returns:
        object: Data decoder
    '''
    if data_type == 2:
        return UrlDecoder()
    else:
        return Df3Decoder()


class UrlDecoder(object):
    '''
    Decodes data from RuuviTag url
    Protocol specification:
    https://github.com/ruuvi/sensor-protocol-for-eddystone-url
    '''

    '''
    Decoder operations are ported from:
    https://github.com/ruuvi/sensor-protocol-for-eddystone-url/blob/master/index.html

    0:   uint8_t     format;          // (0x01 = realtime sensor readings)
    1:   uint8_t     humidity;        // one lsb is 0.5%
    2-3: uint16_t    temperature;     // Signed 8.8 fixed-point notation.
    4-5: uint16_t    pressure;        // (-50kPa)
    6-7: uint16_t    time;            // seconds (now from reset)

    The bytes for temperature, pressure and time are swaped during the encoding
    '''

    def _get_temperature(self, decoded):
        '''Return temperature in celsius'''
        temp = (decoded[2] & 127) + decoded[3] / 100
        sign = (decoded[2] >> 7) & 1
        if sign == 0:
            return round(temp, 2)
        return round(-1 * temp, 2)

    def _get_humidity(self, decoded):
        '''Return humidity %'''
        return decoded[1] * 0.5

    def _get_pressure(self, decoded):
        '''Return air pressure hPa'''
        pres = ((decoded[4] << 8) + decoded[5]) + 50000
        return pres / 100

    def decode_data(self, encoded):
        '''
        Decode sensor data.

        Returns:
            dict: Sensor values
        '''
        try:
            identifier = None
            if len(encoded) > 8:
                identifier = encoded[8:]
                encoded = encoded[:8]
            decoded = bytearray(base64.b64decode(encoded, '-_'))
            return {
                'temperature': self._get_temperature(decoded),
                'humidity': self._get_humidity(decoded),
                'pressure': self._get_pressure(decoded),
                'identifier': identifier
            }
        except:
            log.exception('Encoded value: %s not valid', encoded)
            return None


class Df3Decoder(object):
    '''
    Decodes data from RuuviTag with Data Format 3
    Protocol specification:
    https://github.com/ruuvi/sensor-protocol-for-eddystone-url
    '''

    def _get_temperature(self, data):
        '''Return temperature in celsius'''
        temp = (data[2] << 1 >> 1) + (data[3] / 100)
        sign = (data[2] >> 7) & 1
        if sign == 0:
            return round(temp, 2)
        return round(-1 * temp, 2)

    def _get_humidity(self, data):
        '''Return humidity %'''
        return data[1] * 0.5

    def _get_pressure(self, data):
        '''Return air pressure hPa'''
        pres = (data[4] << 8) + data[5] + 50000
        return pres / 100

    def _twos_complement(self, value, bits):
        if (value & (1 << (bits - 1))) != 0:
            value = value - (1 << bits)
        return value

    def _get_acceleration(self, data):
        '''Return acceleration mG'''
        acc_x = self._twos_complement((data[6] << 8) + data[7], 16)
        acc_y = self._twos_complement((data[8] << 8) + data[9], 16)
        acc_z = self._twos_complement((data[10] << 8) + data[11], 16)
        return (acc_x, acc_y, acc_z)

    def _get_battery(self, data):
        '''Return battery mV'''
        return (data[12] << 8) + data[13]

    def decode_data(self, data):
        '''
        Decode sensor data.

        Returns:
            dict: Sensor values
        '''
        try:
            byte_data = bytearray.fromhex(data)
            acc_x, acc_y, acc_z = self._get_acceleration(byte_data)
            return {
                'humidity': self._get_humidity(byte_data),
                'temperature': self._get_temperature(byte_data),
                'pressure': self._get_pressure(byte_data),
                'acceleration': math.sqrt(acc_x * acc_x + acc_y * acc_y + acc_z * acc_z),
                'acceleration_x': acc_x,
                'acceleration_y': acc_y,
                'acceleration_z': acc_z,
                'battery': self._get_battery(byte_data)
            }
        except Exception:
            log.exception('Value: %s not valid', data)
            return None
