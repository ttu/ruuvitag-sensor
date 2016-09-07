import logging
import re
import sys

from ruuvitag_sensor.url_decoder import UrlDecoder

_LOGGER = logging.getLogger(__name__)

macRegex = '[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$'
ruuviStart = 'ruuvi_'

if sys.platform.startswith('win'):
    from ruuvitag_sensor.ble_communication import BleCommunicationWin
    ble = BleCommunicationWin()
else:
    from ruuvitag_sensor.ble_communication import BleCommunicationNix
    ble = BleCommunicationNix()


class RuuviTagSensor(object):

    def __init__(self, mac, name):

        if not re.match(macRegex, mac.lower()):
            raise ValueError('{} is not valid mac address'.format(mac))

        self._decoder = UrlDecoder()
        self._mac = mac
        self._state = {}
        self._name = name

    @property
    def mac(self):
        return self._mac

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    def update(self):
        data = ble.get_data(self._mac)
        self._state = self._decoder.get_data(data)
        return self._state

    @staticmethod
    def find_ruuvitags():
        return [(address, name) for address, name in ble.find_ble_devices()
                if name.startswith(ruuviStart)]
