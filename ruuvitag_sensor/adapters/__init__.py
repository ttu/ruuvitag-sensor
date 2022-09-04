import abc
from typing import Iterator, List, Tuple


class BleCommunication(object):
    """Bluetooth LE communication"""
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    def get_first_data(mac: str, bt_device: str = '') -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def get_data(blacklist: List[str] = [], bt_device: str = '') -> Iterator[Tuple[str, str]]:
        pass


class BleCommunicationAsync(object):
    """Asynchronous Bluetooth LE communication"""
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    async def get_first_data(mac: str, bt_device: str = '') -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    async def get_data(blacklist: List[str] = [], bt_device: str = '') -> Iterator[Tuple[str, str]]:
        pass
