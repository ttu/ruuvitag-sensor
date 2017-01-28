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

    def __init__(self, mac):

        if not re.match(mac_regex, mac.lower()):
            raise ValueError('{} is not valid mac address'.format(mac))

        self._mac = mac
        self._state = {}
        self._data = None

    @property
    def mac(self):
        return self._mac

    @property
    def state(self):
        return self._state

    @staticmethod
    def get_data(mac):
        raw = ble.get_data(mac)
        return RuuviTagSensor.convert_data(raw)

    @staticmethod
    def convert_data(raw):
        """
        Convert hexadcimal data to string and validate that data is from RuuviTag.
        Encoded data part is after ruu.vi/# or r/

        Returns:
            Encoded sensor data part in string
        """
        try:
            # TODO: Fix conversion so convered data will show https://ruu.vi/# and htts://r/
            # Now it has e.g. ▲☻☺♠♥♥■■►♥ruu.vi/#AjwYAMFc
            base16_split = [raw[i:i + 2] for i in range(0, len(raw), 2)]
            selected_hexs = filter(lambda x: int(x, 16) < 128, base16_split)
            characters = [chr(int(c, 16)) for c in selected_hexs]
            data = ''.join(characters)

            # take only part after ruu.vi/# or r/
            index = data.find('ruu.vi/#')
            if index > -1:
                return data[(index + 8):]
            else:
                index = data.find('r/')
                if index > -1:
                    return data[(index + 2):]
                return None
        except:
            return None

    @staticmethod
    def find_ruuvitags():
        """
        Find all RuuviTags. Function will print the mac and the state of the sensors when found.
        Function will execute as long as it is  stopped. Stop ecexution with Crtl+C.

        Returns:
            Dictionary containing mac and state of found sensors
        """

        print('Finding RuuviTags. Stop with Ctrl+C.')
        datas = dict()
        for ble_data in ble.get_datas():
            # If mac already in datas continue
            if ble_data[0] in datas:
                continue
            encoded = RuuviTagSensor.convert_data(ble_data[1])
            # Check that encoded data is valid ruuvitag data it is sensor data
            if encoded is not None:
                state = UrlDecoder().decode_data(encoded)
                if state is not None:
                    datas[ble_data[0]] = state
                    print(ble_data[0])
                    print(state)

        return datas

    @staticmethod
    def get_data_for_sensors(macs, search_duratio_sec=5):
        """
        Get lates data for sensors in the macs list.

        Args:
            macs: List of mac addresses
            search_duratio_sec: Search duration in seconds. Default 5.
        Returns:
            Dictionary containing mac and state of found sensors
        """

        print('Get latest data for sensors. Search duration is {}s'.format(
            search_duratio_sec))
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
            encoded = RuuviTagSensor.convert_data(ble_data[1])
            # Check that encoded data is valid ruuvitag data it is sensor data
            if encoded is not None:
                state = UrlDecoder().decode_data(encoded)
                if state is not None:
                    datas[ble_data[0]] = state

        return datas

    def update(self):
        """
        Get lates data from the sensor and update own state.

        Returns:
            Latest state
        """

        data = RuuviTagSensor.get_data(self._mac)

        if data == self._data:
            return self._state

        self._data = data

        if self._data is None:
            self._state = {}
        else:
            self._state = UrlDecoder().decode_data(self._data)

        return self._state
