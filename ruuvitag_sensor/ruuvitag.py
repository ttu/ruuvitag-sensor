import re

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.decoder import get_decoder

mac_regex = '[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$'


class RuuviTag(object):
    """
    RuuviTag Sensors object
    """

    def __init__(self, mac, bt_device=''):

        if not re.match(mac_regex, mac.lower()):
            raise ValueError(f'{mac} is not a valid MAC address')

        self._mac = mac
        self._state = {}
        self._data = None
        self._bt_device = bt_device

    @property
    def mac(self):
        return self._mac

    @property
    def state(self):
        return self._state

    def update(self):
        """
        Get latest data from the sensor and update own state.

        Returns:
            dict: Latest state
        """

        (data_format, data) = RuuviTagSensor.get_first_raw_data(self._mac, self._bt_device)

        if data == self._data:
            return self._state

        self._data = data

        if self._data is None:
            self._state = {}
        else:
            self._state = get_decoder(data_format).decode_data(self._data)

        return self._state
