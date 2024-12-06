import argparse
import asyncio
import logging
import sys

import ruuvitag_sensor
from ruuvitag_sensor.adapters import is_async_adapter
from ruuvitag_sensor.log import log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()


def my_excepthook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)

    if not issubclass(exctype, KeyboardInterrupt):
        log.critical(value)


sys.excepthook = my_excepthook


async def _async_main_handle(arguments: argparse.Namespace):
    if arguments.mac_address:
        data = await RuuviTagSensor.get_data_for_sensors_async(
            macs=[arguments.mac_address], bt_device=arguments.bt_device
        )
        log.info(data)
    elif arguments.find_action:
        await RuuviTagSensor.find_ruuvitags_async(arguments.bt_device)
    elif arguments.latest_action:
        data = await RuuviTagSensor.get_data_for_sensors_async(bt_device=arguments.bt_device)
        log.info(data)
    elif arguments.stream_action:
        async for mac, sensor_data in RuuviTagSensor.get_data_async(bt_device=arguments.bt_device):
            log.info("%s - %s", mac, sensor_data)


def _sync_main_handle(arguments: argparse.Namespace):
    if arguments.mac_address:
        data = RuuviTagSensor.get_data_for_sensors(macs=[arguments.mac_address], bt_device=arguments.bt_device)
        log.info(data)
    elif arguments.find_action:
        RuuviTagSensor.find_ruuvitags(arguments.bt_device)
    elif arguments.latest_action:
        data = RuuviTagSensor.get_data_for_sensors(bt_device=arguments.bt_device)
        log.info(data)
    elif arguments.stream_action:
        RuuviTagSensor.get_data(lambda x: log.info("%s - %s", x[0], x[1]), bt_device=arguments.bt_device)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--get", dest="mac_address", help="Get data")
    parser.add_argument("-d", "--device", dest="bt_device", help="Set Bluetooth device id (default hci0)")
    parser.add_argument("-f", "--find", action="store_true", dest="find_action", help="Find broadcasting RuuviTags")
    parser.add_argument(
        "-l", "--latest", action="store_true", dest="latest_action", help="Get latest data for found RuuviTags"
    )
    parser.add_argument(
        "-s", "--stream", action="store_true", dest="stream_action", help="Stream broadcasts from all RuuviTags"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {ruuvitag_sensor.__version__}")
    parser.add_argument("--debug", action="store_true", dest="debug_action", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug_action:
        log.setLevel(logging.DEBUG)
        for handler in log.handlers:
            handler.setLevel(logging.DEBUG)

    if not args.mac_address and not args.find_action and not args.latest_action and not args.stream_action:
        parser.print_usage()
        sys.exit(0)

    if is_async_adapter(ruuvitag_sensor.ruuvi.ble):
        asyncio.run(_async_main_handle(args))
    else:
        _sync_main_handle(args)
