import base64


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
        temp = (((decoded[2] & 127) << 8) | decoded[3])
        sign = (decoded[2] >> 7) & 1
        if sign == 0:
            return round(temp / 256.0, 1)
        return round(-1 * temp / 256.0, 1)

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
            Sensor values in dictionary
        '''
        try:
            decoded = bytearray(base64.b64decode(encoded))
            return {
                'temperature': self._get_temperature(decoded),
                'humidity': self._get_humidity(decoded),
                'pressure': self._get_pressure(decoded)
            }
        except:
            return None

