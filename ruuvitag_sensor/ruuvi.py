import logging

from url_decoder import UrlDecoder
from ble_communication import BleCommunication

_LOGGER = logging.getLogger(__name__)


class RuuviTagSensor(object):

    def __init__(self, mac):
        self._decoder = UrlDecoder()
        self._ble = BleCommunication()
        self._mac = mac
        self._state = None

    @property
    def state(self):
        return self._state

    def update(self):
        data = self._ble.get_data(self._mac)
        self._state = self._decoder.get_data(data)
        return self._state


