import re
from typing import Optional

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.decoder import get_decoder
from ruuvitag_sensor.ruuvi_types import SensorData

mac_regex = '[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$'


class RuuviTag(object):
    """
    RuuviTag Sensors object
    """

    def __init__(self, mac: str, bt_device: str = ''):

        if not re.match(mac_regex, mac.lower()):
            raise ValueError(f'{mac} is not a valid MAC address')

        self._mac: str = mac
        self._state: Optional[SensorData] = None
        self._data: Optional[str] = None
        self._bt_device: str = bt_device

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def state(self) -> Optional[SensorData]:
        return self._state

    def update(self) -> Optional[SensorData]:
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
            self._state = None
        else:
            self._state = get_decoder(data_format).decode_data(self._data)

        return self._state
