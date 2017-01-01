import sys
import argparse

import ruuvitag_sensor
from ruuvi import RuuviTagSensor

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--get', dest='mac_address', help='Get data')
    parser.add_argument('-f', '--find', action='store_true',
                        dest='find_action', help='Find broadcasting RuuviTags')
    parser.add_argument('--version', action='version', 
                        version='%(prog)s {}'.format(ruuvitag_sensor.__version__))
    args = parser.parse_args()

    if args.mac_address:
        sensor = RuuviTagSensor(args.mac_address, '')
        state = sensor.update()
        print(state)
    elif args.find_action:
        tags = RuuviTagSensor.find_ruuvitags()
        print(tags)
    else:
        parser.print_usage()
