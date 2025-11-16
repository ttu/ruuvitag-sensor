import re

from ruuvitag_sensor.decoder import get_decoder
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvi_types import DataFormat, SensorData

mac_regex = "[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$"


class RuuviTagBase:
    """
    RuuviTag Sensors object
    """

    def __init__(self, mac: str, bt_device: str = ""):
        if not re.match(mac_regex, mac.lower()):
            raise ValueError(f"{mac} is not a valid MAC address")

        self._mac: str = mac
        self._state: dict | SensorData = {}
        self._data: str | None = None
        self._bt_device: str = bt_device

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def state(self) -> dict | SensorData:
        return self._state

    def _handle_new_data_and_return_state(self, data_format: DataFormat, data: str | None) -> dict | SensorData:
        if data == self._data:
            return self._state

        self._data = data

        if self._data is None:
            self._state = {}
        elif data_format is not None:
            self._state = get_decoder(data_format).decode_data(self._data)  # type: ignore[assignment]

        return self._state


class RuuviTag(RuuviTagBase):
    def update(self) -> dict | SensorData:
        """
        Get latest data from the sensor and update own state.

        Returns:
            dict: Latest state
        """

        (data_format, raw_data) = RuuviTagSensor.get_first_raw_data(self._mac, self._bt_device)
        return self._handle_new_data_and_return_state(data_format, raw_data)


class RuuviTagAsync(RuuviTagBase):
    """
    NOTE: This class is not working on macOS
    """

    async def update(self) -> dict | SensorData:
        """
        Get latest data from the sensor and update own state.

        Returns:
            dict: Latest state
        """

        (data_format, raw_data) = await RuuviTagSensor.get_first_raw_data_async(self._mac, self._bt_device)
        return self._handle_new_data_and_return_state(data_format, raw_data)
