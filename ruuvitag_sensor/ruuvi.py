from optparse import Option
import sys
import os
import time
import logging
from multiprocessing import Manager
from typing import Callable, Dict, Generator, List, Optional, Tuple
from warnings import warn

from ruuvitag_sensor.data_formats import DataFormats
from ruuvitag_sensor.decoder import get_decoder, parse_mac
from ruuvitag_sensor.ruuvi_types import SensorData

log = logging.getLogger(__name__)

RUUVI_BLE_ADAPTER_ENV = os.environ.get('RUUVI_BLE_ADAPTER', '').lower()


if 'bleak' in RUUVI_BLE_ADAPTER_ENV:
    from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak
    ble = BleCommunicationBleak()
elif 'bleson' in RUUVI_BLE_ADAPTER_ENV:
    from ruuvitag_sensor.adapters.bleson import BleCommunicationBleson
    ble = BleCommunicationBleson()
elif os.environ.get('RUUVI_BLE_ADAPTER') == 'Bluegiga':
    from ruuvitag_sensor.adapters.bluegiga import BleCommunicationBluegiga
    ble = BleCommunicationBluegiga()
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
        running (bool): Defines if the function should continue execution
    """

    running = True


class RuuviTagSensor(object):
    """
    RuuviTag communication functionality
    """

    @staticmethod
    def get_first_raw_data(mac: str, bt_device: str = '') -> Tuple[Optional[int],Optional[str]]:
        """
        Get raw data for selected RuuviTag. This method is intended to be used only by RuuviTag-class.

        Args:
            mac (string): MAC address
            bt_device (string): Bluetooth device id
        Returns:
            tuple (int, string): Data Format type and raw Sensor data
        """

        raw = ble.get_first_data(mac, bt_device)
        return DataFormats.convert_data(raw)

    @staticmethod
    async def get_first_raw_data_async(mac: str, bt_device: str = '') -> Tuple[Optional[int],Optional[str]]:
        """
        Get raw data for selected RuuviTag. This method is intended to be used only by RuuviTag-class.
        It doesn't have asynchronous implementation.

        Args:
            mac (string): MAC address
            bt_device (string): Bluetooth device id
        Returns:
            tuple (int, string): Data Format type and raw Sensor data
        """
        raw = await ble.get_first_data(mac, bt_device)
        return DataFormats.convert_data(raw)

    @staticmethod
    def find_ruuvitags(bt_device: str = '') -> Dict[str, Tuple[Optional[str], SensorData]]:
        """
        CLI helper function.

        Find all RuuviTags. Function will print the MAC and the state of the sensors when found.
        Function will execute as long as it is stopped. Stop ecexution with Ctrl+C.

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
    async def find_ruuvitags_async(bt_device: str = '') -> Dict[str, Tuple[Optional[str], SensorData]]:
        """
        CLI helper function.

        Find all RuuviTags. Function will print the MAC and the state of the sensors when found.
        Function will execute as long as it is stopped. Stop ecexution with Ctrl+C.

        Returns:
            dict: MAC and state of found sensors
        """

        if 'bleak' not in RUUVI_BLE_ADAPTER_ENV:
            raise Exception('Only Bleak BLE communication is supported')

        log.info('Finding RuuviTags. Stop with Ctrl+C.')

        data = {}
        mac_blacklist = Manager().list()
        data_iter = ble.get_data(mac_blacklist, bt_device)

        async for new_data in data_iter:
            if new_data[0] in data:
                continue
            data[new_data[0]] = new_data[1]
            log.info(new_data[0])
            log.info(new_data[1])

        return data

    @staticmethod
    def get_data_for_sensors(macs: List[str] = [], search_duratio_sec: int = 5, bt_device: str = '') -> Dict[str, Tuple[Optional[str], SensorData]]:
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
    async def get_data_async(macs: List[str] = [], bt_device: str = '') -> Generator[Tuple[Optional[str], SensorData], None, None]:
        if 'bleak' not in RUUVI_BLE_ADAPTER_ENV:
            raise Exception('Only Bleak BLE communication is supported')

        mac_blacklist = Manager().list()
        data_iter = ble.get_data(mac_blacklist, bt_device)

        async for ble_data in data_iter:
            data = RuuviTagSensor._parse_data(ble_data, mac_blacklist, macs)

            # Check MAC whitelist if advertised MAC available
            if ble_data[0] and macs and not ble_data[0] in macs:
                log.debug('MAC not whitelisted: %s', ble_data[0])
                continue

            if data:
                yield data

    @staticmethod
    def get_data(callback: Callable[[Tuple[Optional[str], SensorData]], None], macs: List[str] = [], run_flag: RunFlag = RunFlag(), bt_device: str = ''):
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
    def get_datas(callback: Callable[[Tuple[Optional[str], SensorData]], None], macs: List[str] = [], run_flag: RunFlag = RunFlag(), bt_device: str = ''):
        """
        DEPRECATED
        This method will be removed in a future version.
        Use get_data-method instead.
        """
        warn('This method will be removed in a future version, use get_data() instead',
             FutureWarning)
        return RuuviTagSensor.get_data(callback, macs, run_flag, bt_device)

    @staticmethod
    def _get_ruuvitag_data(macs: List[str] = [], search_duratio_sec: Optional[int] = None, run_flag: RunFlag = RunFlag(), bt_device: str = '') -> Generator[Tuple[Optional[str], SensorData], None, None]:
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

            data = RuuviTagSensor._parse_data(ble_data, mac_blacklist, macs)
            if data:
                yield data

    @staticmethod
    def _parse_data(ble_data: Tuple[str, str], mac_blacklist: List[str], macs: List[str] = []) -> Optional[Tuple[Optional[str], SensorData]]:
        (mac, payload) = ble_data
        (data_format, data) = DataFormats.convert_data(payload)
        
        # Check that encoded data is valid RuuviTag data and it is sensor data
        # If data is not valid RuuviTag data add MAC to blacklist if MAC is available
        if data is None:
            if mac:
                log.debug('Blacklisting MAC %s', mac)
                mac_blacklist.append(mac)
            return None

        if data_format is None:
            # Whatever we heard was from a Ruuvitag, but did not contain
            # any measurements. Ignore this.
            return None

        decoded = get_decoder(data_format).decode_data(data)
        if decoded is None:
            log.error('Decoded data is null. MAC: %s - Raw: %s', mac, payload)
            return None

        # If advertised MAC is missing, try to parse it from the payload
        mac_to_send = mac if mac else \
            parse_mac(data_format, decoded['mac']) if 'mac' in decoded and decoded['mac'] is not None else None

        # Check whitelist using MAC from decoded data if advertised MAC is not available
        if mac_to_send and macs and mac_to_send not in macs:
            log.debug('MAC not whitelisted: %s', mac_to_send)
            return None
    
        return (mac_to_send, decoded)
