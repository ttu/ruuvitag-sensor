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
    https://github.com/ruuvi/ruuvi-sensor-protocols
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
    https://github.com/ruuvi/ruuvi-sensor-protocols
    '''

    def _get_temperature(self, data):
        '''Return temperature in celsius'''
        temp = (data[2] & ~(1 << 7)) + (data[3] / 100)
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

class Df5Decoder(object):
    '''
    Decodes data from RuuviTag with Data Format 5
    Protocol specification:
    https://github.com/ruuvi/ruuvi-sensor-protocols
    '''

    def _get_temperature(self, data):
        '''Return temperature in celsius'''
        if (0x7FFF == data[1:2]):
            return None

        temperature = ((data[1]&0x7F) << 8 | data[2] & 0xFF) / 200
        sign = data[1]&0x7F
        if (!sign):
            return round(temp, 2);
        return round(-1 * temp, 2)

    def _get_humidity(self, data):
        '''Return humidity %'''
        if (0xFFFF == data[3:4]):
            return None

        humidity = ((data[3] & 0xFF) << 8 | data[4] & 0xFF) / 400
        return humidity[1] * 0.5

    def _get_pressure(self, data):
        '''Return air pressure hPa'''
        if (0xFFFF == data[5:6]):
            return None

        pressure = ((data[5] & 0xFF) << 8 | data[6] & 0xFF) + 50000
        return pressure / 100

    def _twos_complement(self, value, bits):
        if (value & (1 << (bits - 1))) != 0:
            value = value - (1 << bits)
        return value

    def _get_acceleration(self, data):
        '''Return acceleration mG'''
        if (0x7FFF == data[7:8] or
                   0x7FFF == data[9:10] or
                   0x7FFF == data[11:12]):
            return (None, None, None)

        acc_x = self._twos_complement((data[7] << 8) + data[8], 16)
        acc_y = self._twos_complement((data[9] << 8) + data[10], 16)
        acc_z = self._twos_complement((data[11] << 8) + data[12], 16)
        return (acc_x, acc_y, acc_z)

    def _get_powerinfo(self, data):
        '''Return battery voltage and tx power '''
        power_info = (data[13] & 0xFF) << 8 | (data[14] & 0xFF)
        battery_voltage = (power_info >>> 5) / 1000d + 1.6
        tx_power = (power_info & 0b11111) * 2 - 40

        if ((power_info >>> 5) == 0b11111111111):
            battery_voltage = None
        if ((powerInfo & 0b11111) == 0b11111):
            tx_power = None

        return (battery_voltage, tx_power)

    def _get_battery(self, data):
        '''Return battery mV'''
        battery_voltage, tx_power = self._get_powerinfo(data)
        return battery_voltage

    def _get_txpower(self, data):
        '''Return battery mV'''
        battery_voltage, tx_power = self._get_powerinfo(data)
        return tx_power

    def _get_movementcounter(self, data):
        return (data[15] & 0xFF)

    def _get_measurementsequencenumber(self, data):
        measurementSequenceNumber = (data[16] & 0xFF) << 8 | data[17] & 0xFF;
        return measurementSequenceNumber

    def _get_mac(self, data):
        return ''.join('{:02x}'.format(x) for x in data[18:23])

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
                'tx_power': self._get_txpower(byte_data),
                'battery': self._get_battery(byte_data),
                'movementcounter': self._get_movementcounter(byte_data),
                'measurementsequencenumber': self._get_measurementsequencenumber(byte_data),
                'mac': self._get_mac(byte_data);
            }
        except Exception:
            log.exception('Value: %s not valid', data)
            return None

