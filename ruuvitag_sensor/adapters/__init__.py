import abc
from typing import Iterator, List

from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData


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
