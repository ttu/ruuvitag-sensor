import sys
import argparse

import ruuvitag_sensor
from ruuvitag_sensor.log import log
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvitag import RuuviTag

ruuvitag_sensor.log.enable_console()


def my_excepthook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)

    if not issubclass(exctype, KeyboardInterrupt):
        log.critical(value)


sys.excepthook = my_excepthook

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--get', dest='mac_address', help='Get data')
    parser.add_argument('-d', '--device', dest='bt_device',
                        help='Set Bluetooth device id (default hci0)')
    parser.add_argument('-f', '--find', action='store_true',
                        dest='find_action', help='Find broadcasting RuuviTags')
    parser.add_argument('-l', '--latest', action='store_true',
                        dest='latest_action', help='Get latest data for found RuuviTags')
    parser.add_argument('-s', '--stream', action='store_true',
                        dest='stream_action', help='Stream broadcasts from all RuuviTags')
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(ruuvitag_sensor.__version__))
    args = parser.parse_args()

    if args.mac_address:
        sensor = RuuviTag(args.mac_address, args.bt_device)
        state = sensor.update()
        log.info(state)
    elif args.find_action:
        RuuviTagSensor.find_ruuvitags(args.bt_device)
    elif args.latest_action:
        datas = RuuviTagSensor.get_data_for_sensors(bt_device=args.bt_device)
        log.info(datas)
    elif args.stream_action:
        RuuviTagSensor.get_datas(
            lambda x: log.info('%s - %s', x[0], x[1]),
            bt_device=args.bt_device)
    else:
        parser.print_usage()
