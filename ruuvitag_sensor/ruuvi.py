import logging
import re
import sys
import os

from ruuvitag_sensor.url_decoder import UrlDecoder

_LOGGER = logging.getLogger(__name__)

macRegex = '[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$'

if not sys.platform.startswith('linux') or os.environ.get('CI') == 'True':
    # Use BleCommunicationDummy also for CI as it can't use gattlib
    from ruuvitag_sensor.ble_communication import BleCommunicationDummy
    ble = BleCommunicationDummy()
else:
    from ruuvitag_sensor.ble_communication import BleCommunicationNix
    ble = BleCommunicationNix()


class RuuviTagSensor(object):

    def __init__(self, mac, name):

        if not re.match(macRegex, mac.lower()):
            raise ValueError('{} is not valid mac address'.format(mac))

        self._mac = mac
        self._state = {}
        self._name = name
        self._data = None

    @property
    def mac(self):
        return self._mac

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @staticmethod
    def get_data(mac):
        raw = ble.get_data(mac)
        return RuuviTagSensor.decode_data(raw)

    @staticmethod
    def decode_data(raw):
        try:
            line = raw[4:]
            base16_split = [line[i:i + 2] for i in range(0, len(line), 2)]
            characters = [chr(int(c, 16)) for c in base16_split]
            data = ''.join(characters)

            if 'ruu.vi' in data:
                # take only part after ruu.vi#
                return ''.join(characters[20:])
            else:
                return None
        except:
            return None

    @staticmethod
    def find_ruuvitags():
        print('Finding RuuviTags. Stop with Ctrl+C.')
        datas = dict()
        for ble_data in ble.get_datas():
            decoded = RuuviTagSensor.decode_data(ble_data[1])
            if decoded is not None:
                state = UrlDecoder().get_data(decoded)
                if not ble_data[0] in datas:
                    datas[ble_data[0]] = state
                    print(ble_data[0])
                    print(state)

        return datas

    def update(self):
        data = RuuviTagSensor.get_data(self._mac)

        if data == self._data:
            return self._state

        self._data = data

        if self._data is None:
            self._state = {}
        else:
            self._state = UrlDecoder().get_data(self._data)

        return self._state
