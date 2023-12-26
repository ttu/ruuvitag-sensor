import abc
import os
import sys
from typing import AsyncGenerator, Generator, List

from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData

# pylint: disable=import-outside-toplevel, cyclic-import, too-many-return-statements


def get_ble_adapter():
    forced_ble_adapter = os.environ.get("RUUVI_BLE_ADAPTER", "").lower()
    use_ruuvi_nix_from_file = "RUUVI_NIX_FROMFILE" in os.environ
    is_ci_env = "CI" in os.environ

    if forced_ble_adapter:
        if "bleak" in forced_ble_adapter:
            from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak

            return BleCommunicationBleak()
        if "bleson" in forced_ble_adapter:
            from ruuvitag_sensor.adapters.bleson import BleCommunicationBleson

            return BleCommunicationBleson()
        if "bluez" in forced_ble_adapter:
            from ruuvitag_sensor.adapters.nix_hci import BleCommunicationNix

            return BleCommunicationNix()

        raise RuntimeError(f"Unknown BLE adapter: {forced_ble_adapter}")

    if use_ruuvi_nix_from_file:
        # Emulate BleCommunicationNix by reading hcidump data from a file
        from ruuvitag_sensor.adapters.nix_hci_file import BleCommunicationNixFile

        return BleCommunicationNixFile()

    if is_ci_env:
        # Use BleCommunicationDummy for CI as it can't use BlueZ
        from ruuvitag_sensor.adapters.dummy import BleCommunicationDummy

        return BleCommunicationDummy()

    # Use default adapter for platform
    if sys.platform.startswith("win") or sys.platform.startswith("darwin"):
        from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak

        return BleCommunicationBleak()

    # BlueZ is default for Linux
    from ruuvitag_sensor.adapters.nix_hci import BleCommunicationNix

    return BleCommunicationNix()


def is_async_adapter(ble: object):
    return issubclass(type(ble), BleCommunicationAsync)


def is_async_from_env():
    return "bleak" in os.environ.get("RUUVI_BLE_ADAPTER", "").lower()


def throw_if_not_sync_adapter(ble: object):
    if is_async_adapter(ble):
        raise RuntimeError("Sync BLE adapter required")


def throw_if_not_async_adapter(ble: object):
    if not is_async_adapter(ble):
        raise RuntimeError("Async BLE adapter required")


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
