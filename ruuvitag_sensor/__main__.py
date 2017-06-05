import sys
import argparse
import logging

import ruuvitag_sensor
import ruuvitag_sensor.log
from ruuvi import RuuviTagSensor
from log import configureLog  # pylint: disable=E0611

configureLog(True)

log = logging.getLogger('ruuvitag_sensor')


def my_excepthook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)

    if not issubclass(exctype, KeyboardInterrupt):
        log.critical(value)

sys.excepthook = my_excepthook

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--get', dest='mac_address', help='Get data')
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
        sensor = RuuviTagSensor(args.mac_address)
        state = sensor.update()
        log.info(state)
    elif args.find_action:
        RuuviTagSensor.find_ruuvitags()
    elif args.latest_action:
        datas = RuuviTagSensor.get_data_for_sensors()
        log.info(datas)
    elif args.stream_action:
        RuuviTagSensor.get_datas(lambda x: log.info('%s - %s' % (x[0], x[1])))
    else:
        parser.print_usage()
