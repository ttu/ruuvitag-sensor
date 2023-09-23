import logging
import time
from multiprocessing import Manager
from multiprocessing.managers import ListProxy
from typing import AsyncGenerator, Callable, Dict, Generator, List, Optional
from warnings import warn

from ruuvitag_sensor.adapters import get_ble_adapter, throw_if_not_async_adapter, throw_if_not_sync_adapter
from ruuvitag_sensor.data_formats import DataFormats
from ruuvitag_sensor.decoder import get_decoder, parse_mac
from ruuvitag_sensor.ruuvi_types import DataFormatAndRawSensorData, Mac, MacAndRawData, MacAndSensorData, SensorData

log = logging.getLogger(__name__)
ble = get_ble_adapter()


class RunFlag:
    """
    Wrapper for boolean run flag

    Attributes:
        running (bool): Defines if the function should continue execution
    """

    running = True


class RuuviTagSensor:
    """
    RuuviTag communication functionality
    """

    @staticmethod
    def get_first_raw_data(mac: str, bt_device: str = "") -> DataFormatAndRawSensorData:
        """
        Get raw data for selected RuuviTag. This method is intended to be used only by
        RuuviTag-class.

        Args:
            mac (string): MAC address
            bt_device (string): Bluetooth device id
        Returns:
            tuple (int, string): Data Format type and raw Sensor data
        """
        throw_if_not_sync_adapter(ble)

        raw = ble.get_first_data(mac, bt_device)
        return DataFormats.convert_data(raw)

    @staticmethod
    async def get_first_raw_data_async(mac: str, bt_device: str = "") -> DataFormatAndRawSensorData:
        """
        Get raw data for selected RuuviTag. This method is intended to be used only by
        RuuviTagAsync-class.

        NOTE: This method is not working on macOS

        Args:
            mac (string): MAC address
            bt_device (string): Bluetooth device id
        Returns:
            tuple (int, string): Data Format type and raw Sensor data
        """
        throw_if_not_async_adapter(ble)

        raw = await ble.get_first_data(mac, bt_device)
        return DataFormats.convert_data(raw)

    @staticmethod
    def find_ruuvitags(bt_device: str = "") -> Dict[Mac, SensorData]:
        """
        CLI helper function.

        Find all RuuviTags. Function will print the MAC and the state of the sensors when found.
        Function will execute as long as it is stopped. Stop execution with Ctrl+C.

        Returns:
            dict: MAC and state of found sensors
        """
        throw_if_not_sync_adapter(ble)

        log.info("Finding RuuviTags. Stop with Ctrl+C.")

        data: Dict[str, SensorData] = {}
        for new_data in RuuviTagSensor._get_ruuvitag_data(bt_device=bt_device):
            mac, sensor_data = new_data
            if not mac or mac in data:
                continue
            data[mac] = sensor_data
            log.info(mac)
            log.info(sensor_data)

        return data

    @staticmethod
    async def find_ruuvitags_async(bt_device: str = "") -> Dict[Mac, MacAndSensorData]:
        """
        CLI helper function.

        Find all RuuviTags. Function will print the MAC and the state of the sensors when found.
        Function will execute as long as it is stopped. Stop execution with Ctrl+C.

        Returns:
            dict: MAC and state of found sensors
        """
        throw_if_not_async_adapter(ble)

        log.info("Finding RuuviTags. Stop with Ctrl+C.")

        data: Dict[Mac, MacAndSensorData] = {}
        mac_blacklist = Manager().list()
        data_iter = ble.get_data(mac_blacklist, bt_device)

        async for new_data in data_iter:
            if new_data[0] in data:
                continue

            parsed_data = RuuviTagSensor._parse_data(new_data, mac_blacklist)
            if parsed_data:
                data[new_data[0]] = parsed_data
                log.info(new_data[0])
                log.info(parsed_data)

        return data

    @staticmethod
    def get_data_for_sensors(
        macs: List[str] = [], search_duratio_sec: int = 5, bt_device: str = ""
    ) -> Dict[Mac, SensorData]:
        """
        Get latest data for sensors in the MAC address list.

        Args:
            macs (array): MAC addresses
            search_duratio_sec (int): Search duration in seconds. Default 5
            bt_device (string): Bluetooth device id
        Returns:
            dict: MAC and state of found sensors
        """
        throw_if_not_sync_adapter(ble)

        log.info("Get latest data for sensors. Stop with Ctrl+C.")
        log.info("Stops automatically in %ss", search_duratio_sec)
        log.info("MACs: %s", macs)

        data: Dict[Mac, SensorData] = {}

        for new_data in RuuviTagSensor._get_ruuvitag_data(macs, search_duratio_sec, bt_device=bt_device):
            mac, sensor_data = new_data
            data[mac] = sensor_data

        return data

    @staticmethod
    async def get_data_for_sensors_async(
        macs: List[str] = [], search_duratio_sec: int = 5, bt_device: str = ""
    ) -> Dict[Mac, SensorData]:
        """
        Get latest data for sensors in the MAC address list.

        Args:
            macs (array): MAC addresses
            search_duratio_sec (int): Search duration in seconds. Default 5
            bt_device (string): Bluetooth device id
        Returns:
            dict: MAC and state of found sensors
        """
        throw_if_not_async_adapter(ble)

        log.info("Get latest data for sensors. Stop with Ctrl+C.")
        log.info("Stops automatically in %ss", search_duratio_sec)
        log.info("MACs: %s", macs)

        data: Dict[Mac, SensorData] = {}
        start_time = time.time()

        async for new_data in RuuviTagSensor.get_data_async(macs, bt_device):
            mac, sensor_data = new_data
            data[mac] = sensor_data
            if search_duratio_sec and time.time() - start_time > search_duratio_sec:
                break

        return data

    @staticmethod
    async def get_data_async(macs: List[str] = [], bt_device: str = "") -> AsyncGenerator[MacAndSensorData, None]:
        """
        Get data for all ruuvitag sensors or sensors in the MAC's list.

        Args:
            macs (list): MAC addresses
            bt_device (string): Bluetooth device id
        Returns:
            AsyncGenerator: MAC and State of RuuviTag sensor data (tuple)
        """
        throw_if_not_async_adapter(ble)

        mac_blacklist = Manager().list()
        data_iter = ble.get_data(mac_blacklist, bt_device)

        async for ble_data in data_iter:
            data = RuuviTagSensor._parse_data(ble_data, mac_blacklist, macs)

            # Check MAC whitelist if advertised MAC available
            if ble_data[0] and macs and not ble_data[0] in macs:
                log.debug("MAC not whitelisted: %s", ble_data[0])
                continue

            if data:
                yield data

    @staticmethod
    def get_data(
        callback: Callable[[MacAndSensorData], None],
        macs: List[str] = [],
        run_flag: RunFlag = RunFlag(),
        bt_device: str = "",
    ) -> None:
        """
        Get data for all ruuvitag sensors or sensors in the MAC's list.

        Args:
            callback (func): callback function to be called when new data is received
            macs (list): MAC addresses
            run_flag (object): RunFlag object. Function executes while run_flag.running
            bt_device (string): Bluetooth device id
        """
        throw_if_not_sync_adapter(ble)

        log.info("Get latest data for sensors. Stop with Ctrl+C.")
        log.info("MACs: %s", macs)

        for new_data in RuuviTagSensor._get_ruuvitag_data(macs, None, run_flag, bt_device):
            callback(new_data)

    @staticmethod
    def get_datas(
        callback: Callable[[MacAndSensorData], None],
        macs: List[str] = [],
        run_flag: RunFlag = RunFlag(),
        bt_device: str = "",
    ) -> None:
        """
        DEPRECATED
        This method will be removed in a future version.
        Use get_data-method instead.
        """
        warn("This method will be removed in a future version, use get_data() instead", FutureWarning)
        throw_if_not_sync_adapter(ble)
        return RuuviTagSensor.get_data(callback, macs, run_flag, bt_device)

    @staticmethod
    def _get_ruuvitag_data(
        macs: List[str] = [],
        search_duratio_sec: Optional[int] = None,
        run_flag: RunFlag = RunFlag(),
        bt_device: str = "",
    ) -> Generator[MacAndSensorData, None, None]:
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
                data_iter.close()
                break
            # Check running flag
            if not run_flag.running:
                data_iter.close()
                break
            # Check MAC whitelist if advertised MAC available
            if ble_data[0] and macs and not ble_data[0] in macs:
                log.debug("MAC not whitelisted: %s", ble_data[0])
                continue

            data = RuuviTagSensor._parse_data(ble_data, mac_blacklist, macs)
            if data:
                yield data

    @staticmethod
    def _parse_data(
        ble_data: MacAndRawData, mac_blacklist: ListProxy, allowed_macs: List[str] = []
    ) -> Optional[MacAndSensorData]:
        (mac, payload) = ble_data
        (data_format, data) = DataFormats.convert_data(payload)

        # Check that encoded data is valid RuuviTag data and it is sensor data
        # If data is not valid RuuviTag data add MAC to blacklist if MAC is available
        if data is None:
            if mac:
                log.debug("Blacklisting MAC %s", mac)
                mac_blacklist.append(mac)
            return None

        if data_format is None:
            # Whatever we heard was from a Ruuvitag, but did not contain
            # any measurements. Ignore this.
            return None

        decoded = get_decoder(data_format).decode_data(data)
        if decoded is None:
            log.error("Decoded data is null. MAC: %s - Raw: %s", mac, payload)
            return None

        # If advertised MAC is missing, try to parse it from the payload
        mac_to_send = (
            mac
            if mac
            else parse_mac(data_format, decoded["mac"])
            if "mac" in decoded and decoded["mac"] is not None
            else ""
        )

        # Check whitelist using MAC from decoded data if advertised MAC is not available
        if allowed_macs and mac_to_send not in allowed_macs:
            log.debug("MAC not whitelisted: %s", mac_to_send)
            return None

        return (mac_to_send, decoded)
