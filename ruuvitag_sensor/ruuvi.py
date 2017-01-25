import re
import sys
import os
import time

from ruuvitag_sensor.url_decoder import UrlDecoder

mac_regex = '[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$'

if not sys.platform.startswith('linux') or os.environ.get('CI') == 'True':
    # Use BleCommunicationDummy also for CI as it can't use gattlib
    from ruuvitag_sensor.ble_communication import BleCommunicationDummy
    ble = BleCommunicationDummy()
else:
    from ruuvitag_sensor.ble_communication import BleCommunicationNix
    ble = BleCommunicationNix()


# TODO: Split this class to common functions and RuuviTagSensor

class RuuviTagSensor(object):

    def __init__(self, mac, name):

        if not re.match(mac_regex, mac.lower()):
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
            # TODO: Figure out how to do this properly
            base16_split = [raw[i:i + 2] for i in range(0, len(raw), 2)]
            selected_hexs = filter(lambda x: int(x, 16) < 128, base16_split)
            characters = [chr(int(c, 16)) for c in selected_hexs]
            data = ''.join(characters)
            # take only part after ruu.vi/#
            index = data.index('ruu.vi/#') + 8
            if index > -1:
                return data[index:]
            else:
                return None
        except:
            return None

    @staticmethod
    def find_ruuvitags():
        print('Finding RuuviTags. Stop with Ctrl+C.')
        datas = dict()
        for ble_data in ble.get_datas():
            # If mac already in datas continue
            if ble_data[0] in datas:
                continue
            decoded = RuuviTagSensor.decode_data(ble_data[1])
            # Check that decoded data is valid ruuvitag data it is sensor data
            if decoded is not None:
                state = UrlDecoder().get_data(decoded)
                if state is not None:
                    datas[ble_data[0]] = state
                    print(ble_data[0])
                    print(state)

        return datas

    @staticmethod
    def get_data_for_sensors(macs, search_duratio_sec=5):
        """
        Get lates data for sensors in the macs list.
        Search duration is search_duratio_sec seconds. Default 5 seconds.
        """

        print('Get latest data for sensors. Search duration is {}s'.format(search_duratio_sec))
        print('MACs: {}'.format(macs))

        start_time = time.time()
        datas = dict()
        data_iter = ble.get_datas()

        for ble_data in data_iter:
            if time.time() - start_time > search_duratio_sec:
                data_iter.send(StopIteration)
                break
            # If mac in whitelist
            if not ble_data[0] in macs:
                continue
            decoded = RuuviTagSensor.decode_data(ble_data[1])
            # Check that decoded data is valid ruuvitag data it is sensor data
            if decoded is not None:
                state = UrlDecoder().get_data(decoded)
                if state is not None:
                    datas[ble_data[0]] = state

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
