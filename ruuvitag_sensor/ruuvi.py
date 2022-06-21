import sys
import os
import time
import logging
from multiprocessing import Manager
from warnings import warn

from ruuvitag_sensor.data_formats import DataFormats
from ruuvitag_sensor.decoder import get_decoder, parse_mac

log = logging.getLogger(__name__)


if os.environ.get('RUUVI_BLE_ADAPTER') == 'Bleson':
    from ruuvitag_sensor.adapters.bleson import BleCommunicationBleson
    ble = BleCommunicationBleson()
elif 'RUUVI_NIX_FROMFILE' in os.environ:
    # Emulate BleCommunicationNix by reading hcidump data from a file
    from ruuvitag_sensor.adapters.nix_hci_file import BleCommunicationNixFile
    ble = BleCommunicationNixFile()
elif not sys.platform.startswith('linux') or 'CI' in os.environ:
    # Use BleCommunicationDummy also for CI as it can't use bluez
    from ruuvitag_sensor.adapters.dummy import BleCommunicationDummy
    ble = BleCommunicationDummy()
else:
    from ruuvitag_sensor.adapters.nix_hci import BleCommunicationNix
    ble = BleCommunicationNix()


class RunFlag(object):
    """
    Wrapper for boolean run flag

    Attributes:
        running (bool): Defines if function should continue execution
    """

    running = True


class RuuviTagSensor(object):
    """
    RuuviTag communication functionality
    """

    @staticmethod
    def get_first_raw_data(mac, bt_device=''):
        """
        Get raw data for selected RuuviTag

        Args:
            mac (string): MAC address
            bt_device (string): Bluetooth device id
        Returns:
            tuple (int, string): Data Format type and raw Sensor data
        """

        raw = ble.get_first_data(mac, bt_device)
        return DataFormats.convert_data(raw)

    @staticmethod
    def find_ruuvitags(bt_device=''):
        """
        Find all RuuviTags. Function will print the mac and the state of the sensors when found.
        Function will execute as long as it is stopped. Stop ecexution with Crtl+C.

        Returns:
            dict: MAC and state of found sensors
        """

        log.info('Finding RuuviTags. Stop with Ctrl+C.')

        data = {}
        for new_data in RuuviTagSensor._get_ruuvitag_data(bt_device=bt_device):
            if new_data[0] in data:
                continue
            data[new_data[0]] = new_data[1]
            log.info(new_data[0])
            log.info(new_data[1])

        return data

    @staticmethod
    def get_data_for_sensors(macs=[], search_duratio_sec=5, bt_device=''):
        """
        Get latest data for sensors in the MAC address list.

        Args:
            macs (array): MAC addresses
            search_duratio_sec (int): Search duration in seconds. Default 5
            bt_device (string): Bluetooth device id
        Returns:
            dict: MAC and state of found sensors
        """

        log.info('Get latest data for sensors. Stop with Ctrl+C.')
        log.info('Stops automatically in %ss', search_duratio_sec)
        log.info('MACs: %s', macs)

        data = {}

        for new_data in RuuviTagSensor._get_ruuvitag_data(
                macs,
                search_duratio_sec,
                bt_device=bt_device):
            data[new_data[0]] = new_data[1]

        return data

    @staticmethod
    def get_data(callback, macs=[], run_flag=RunFlag(), bt_device=''):
        """
        Get data for all ruuvitag sensors or sensors in the MAC's list.

        Args:
            callback (func): callback function to be called when new data is received
            macs (list): MAC addresses
            run_flag (object): RunFlag object. Function executes while run_flag.running
            bt_device (string): Bluetooth device id
        """

        log.info('Get latest data for sensors. Stop with Ctrl+C.')
        log.info('MACs: %s', macs)

        for new_data in RuuviTagSensor._get_ruuvitag_data(macs, None, run_flag, bt_device):
            callback(new_data)

    @staticmethod
    def get_datas(callback, macs=[], run_flag=RunFlag(), bt_device=''):
        """
        DEPRECATED
        This method will be removed in a future version.
        Use get_data-method instead.
        """
        warn('This method will be removed in a future version, use get_data() instead',
             FutureWarning)
        return RuuviTagSensor.get_data(callback, macs, run_flag, bt_device)

    @staticmethod
    def _get_ruuvitag_data(macs=[], search_duratio_sec=None, run_flag=RunFlag(), bt_device=''):
        """
        Get data from BluetoothCommunication and handle data encoding.

        Args:
            macs (list): MAC addresses. Default empty list
            search_duratio_sec (int): Search duration in seconds. Default None
            run_flag (object): RunFlag object. Function executes while run_flag.running.
                               Default new RunFlag
            bt_device (string): Bluetooth device id
        Yields:
            tuple: MAC and State of RuuviTag sensor data
        """

        mac_blacklist = Manager().list()
        start_time = time.time()
        data_iter = ble.get_data(mac_blacklist, bt_device)

        for ble_data in data_iter:
            # Check duration
            if search_duratio_sec and time.time() - start_time > search_duratio_sec:
                data_iter.send(StopIteration)
                break
            # Check running flag
            if not run_flag.running:
                data_iter.send(StopIteration)
                break
            # Check MAC whitelist if advertised MAC available
            if ble_data[0] and macs and not ble_data[0] in macs:
                log.debug('MAC not whitelisted: %s', ble_data[0])
                continue

            (data_format, data) = DataFormats.convert_data(ble_data[1])
            # Check that encoded data is valid RuuviTag data and it is sensor data
            # If data is not valid RuuviTag data add MAC to blacklist if MAC is available
            if data is not None:
                if data_format is None:
                    # Whatever we heard was from a Ruuvitag, but did not contain
                    # any measurements. Ignore this.
                    continue

                decoded = get_decoder(data_format).decode_data(data)
                if decoded is not None:
                    # If advertised MAC is missing, try to parse it from the payload
                    mac = ble_data[0] if ble_data[0] else \
                        parse_mac(data_format, decoded['mac']) if decoded['mac'] else None
                    # Check whitelist using MAC from decoded data if advertised MAC is not available
                    if mac and macs and mac not in macs:
                        log.debug('MAC not whitelisted: %s', ble_data[0])
                        continue
                    yield (mac, decoded)
                else:
                    log.error('Decoded data is null. MAC: %s - Raw: %s', ble_data[0], ble_data[1])
            else:
                if ble_data[0]:
                    log.debug("Blacklisting MAC %s", ble_data[0])
                    mac_blacklist.append(ble_data[0])
