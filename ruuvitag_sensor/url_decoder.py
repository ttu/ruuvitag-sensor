import base91


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
        temp = (((decoded[3] & 127) << 8) | decoded[2])
        sign = (decoded[3] >> 7) & 1
        if sign == 0:
            return round(temp / 256.0, 1)
        return round(-1 * temp / 256.0, 1)

    def _get_humidity(self, decoded):
        '''Return humidity %'''
        return decoded[1] * 0.5

    def _get_pressure(self, decoded):
        '''Return air pressure hPa'''
        pres = ((decoded[5] << 8) + decoded[4]) + 50000
        return pres / 100

    def _get_time_elapsed(self, decoded):
        '''Return time in seconds'''
        if len(decoded) > 7:
            return (decoded[7] << 8) + decoded[6]
        return decoded[6]

    def get_data(self, encoded):
        '''Get decoded sensor values in dictionary'''
        decoded = base91.decode(encoded)

        return {
            'temperature': self._get_temperature(decoded),
            'humidity': self._get_humidity(decoded),
            'pressure': self._get_pressure(decoded),
            'elapsed': self._get_time_elapsed(decoded)
        }
