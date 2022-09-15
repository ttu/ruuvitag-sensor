import abc
import os
import sys
from typing import Iterator, List

from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData


def get_ble_adapter():
    if 'bleak' in os.environ.get('RUUVI_BLE_ADAPTER', '').lower():
        from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak
        return BleCommunicationBleak()
    elif 'bleson' in os.environ.get('RUUVI_BLE_ADAPTER', '').lower():
        from ruuvitag_sensor.adapters.bleson import BleCommunicationBleson
        return BleCommunicationBleson()
    elif 'bluegiga' in os.environ.get('RUUVI_BLE_ADAPTER', '').lower():
        from ruuvitag_sensor.adapters.bluegiga import BleCommunicationBluegiga
        return BleCommunicationBluegiga()
    elif 'RUUVI_NIX_FROMFILE' in os.environ:
        # Emulate BleCommunicationNix by reading hcidump data from a file
        from ruuvitag_sensor.adapters.nix_hci_file import BleCommunicationNixFile
        return BleCommunicationNixFile()
    elif not sys.platform.startswith('linux') or 'CI' in os.environ:
        # Use BleCommunicationDummy also for CI as it can't use bluez
        from ruuvitag_sensor.adapters.dummy import BleCommunicationDummy
        return BleCommunicationDummy()
    else:
        from ruuvitag_sensor.adapters.nix_hci import BleCommunicationNix
        return BleCommunicationNix()


def is_async_adapter(ble: object):
    return issubclass(type(ble), BleCommunicationAsync)


class BleCommunication(object):
    """Bluetooth LE communication"""
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    def get_first_data(mac: str, bt_device: str = '') -> RawData:
        pass

    @staticmethod
    @abc.abstractmethod
    def get_data(blacklist: List[str] = [], bt_device: str = '') -> Iterator[MacAndRawData]:
        pass


class BleCommunicationAsync(object):
    """Asynchronous Bluetooth LE communication"""
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    async def get_first_data(mac: str, bt_device: str = '') -> RawData:
        pass

    @staticmethod
    @abc.abstractmethod
    async def get_data(blacklist: List[str] = [], bt_device: str = '') -> Iterator[MacAndRawData]:
        pass
