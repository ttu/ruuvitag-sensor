import sys
import argparse

import ruuvitag_sensor
from ruuvi import RuuviTagSensor
from log import logger


def my_excepthook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)

    if not issubclass(exctype, KeyboardInterrupt):
        logger.critical(value)

sys.excepthook = my_excepthook

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--get', dest='mac_address', help='Get data')
    parser.add_argument('-f', '--find', action='store_true',
                        dest='find_action', help='Find broadcasting RuuviTags')
    parser.add_argument('--version', action='version', 
                        version='%(prog)s {}'.format(ruuvitag_sensor.__version__))
    args = parser.parse_args()

    if args.mac_address:
        sensor = RuuviTagSensor(args.mac_address)
        state = sensor.update()
        print(state)
    elif args.find_action:
        RuuviTagSensor.find_ruuvitags()
    else:
        parser.print_usage()
