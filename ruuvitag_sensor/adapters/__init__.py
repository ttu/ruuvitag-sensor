import abc
import os
import sys
from typing import AsyncGenerator, Generator, List

from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData

# pylint: disable=import-outside-toplevel, cyclic-import


def get_ble_adapter():
    if "bleak" in os.environ.get("RUUVI_BLE_ADAPTER", "").lower():
        from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak

        return BleCommunicationBleak()
    if "bleson" in os.environ.get("RUUVI_BLE_ADAPTER", "").lower():
        from ruuvitag_sensor.adapters.bleson import BleCommunicationBleson

        return BleCommunicationBleson()
    if "RUUVI_NIX_FROMFILE" in os.environ:
        # Emulate BleCommunicationNix by reading hcidump data from a file
        from ruuvitag_sensor.adapters.nix_hci_file import BleCommunicationNixFile

        return BleCommunicationNixFile()
    if not sys.platform.startswith("linux") or "CI" in os.environ:
        # Use BleCommunicationDummy also for CI as it can't use bluez
        from ruuvitag_sensor.adapters.dummy import BleCommunicationDummy

        return BleCommunicationDummy()

    from ruuvitag_sensor.adapters.nix_hci import BleCommunicationNix

    return BleCommunicationNix()


def is_async_adapter(ble: object):
    return issubclass(type(ble), BleCommunicationAsync)


class BleCommunication:
    """Bluetooth LE communication"""

    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    def get_first_data(mac: str, bt_device: str = "") -> RawData:
        pass

    @staticmethod
    @abc.abstractmethod
    def get_data(blacklist: List[str] = [], bt_device: str = "") -> Generator[MacAndRawData, None, None]:
        pass


class BleCommunicationAsync:
    """Asynchronous Bluetooth LE communication"""

    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    async def get_first_data(mac: str, bt_device: str = "") -> RawData:
        pass

    @staticmethod
    @abc.abstractmethod
    async def get_data(blacklist: List[str] = [], bt_device: str = "") -> AsyncGenerator[MacAndRawData, None]:
        raise NotImplementedError("must implement get_data()")
        # https://github.com/python/mypy/issues/5070
        # if False: yield is a mypy fix for
        # error: Return type "AsyncGenerator[Tuple[str, str], None]" of "get_data" incompatible with return type
        # "Coroutine[Any, Any, AsyncGenerator[Tuple[str, str], None]]" in supertype "BleCommunicationAsync"
        if False:  # pylint: disable=unreachable,using-constant-test
            yield 0
