'''
Verification script for RuuviTags

Run the script with Python 3.x and 2.7. Requires at least one active RuuviTag.
'''

import time

from ruuvitag_sensor.decoder import UrlDecoder, Df3Decoder
from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag
from ruuvitag_sensor.ruuvitag import RuuviTag
from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive

# Uncomment to turn on console print
# import ruuvitag_sensor
# from ruuvitag_sensor.log import log
# ruuvitag_sensor.log.enable_console()


#
# Helper Functions
#
def print_header(name):
    print('############################################')
    print(name)
    print('############################################')


def wait_for_finish(run_flag, name):
    max_time = 20

    while run_flag.running:
        time.sleep(0.1)
        max_time -= 0.1
        if max_time < 0:
            raise Exception('%s not finished' % name)


#
# UrlDecoder.decode_data
#
print_header('UrlDecoder.decode_data')

decoder = UrlDecoder()
data = decoder.decode_data('AjwYAMFc')
print(data)

if not data['temperature']:
    raise Exception('FAILED')
else:
    print('OK')


#
# UrlDecoder.decode_data
#
print_header('UrlDecoder.decode_data')

decoder = Df3Decoder()
data = decoder.decode_data('03291A1ECE1EFC18F94202CA0B5300000000BB')
print(data)

if not data['temperature']:
    raise Exception('FAILED')
else:
    print('OK')


#
# RuuviTagSensor.get_data_for_sensors
#
print_header('RuuviTagSensor.get_data_for_sensors')

datas = RuuviTagSensor.get_data_for_sensors(search_duratio_sec=15)
print(datas)

if not datas:
    raise Exception('FAILED')
else:
    print('OK')


#
# RuuviTagSensor.get_data_for_sensors with macs
#
print_header('RuuviTagSensor.get_data_for_sensors with macs')

datas = RuuviTagSensor.get_data_for_sensors(list(datas.keys())[0], search_duratio_sec=15)
print(datas)

if not datas:
    raise Exception('FAILED')
else:
    print('OK')


#
# RuuviTag.update
#
print_header('RuuviTag.update')

tag = RuuviTag(list(datas.keys())[0])
tag.update()
print(tag.state)

if not tag.state:
    raise Exception('FAILED')
else:
    print('OK')


#
# RuuviTagSensor.get_datas
#
print_header('RuuviTagSensor.get_datas')

flag = RunFlag()


def handle_data(found_data):
    flag.running = False
    if not found_data:
        raise Exception('FAILED')
    else:
        print('OK')

RuuviTagSensor.get_datas(handle_data, run_flag=flag)

wait_for_finish(flag, 'RuuviTagSensor.get_datas')


#
# ruuvi_rx.subscribe
#
print_header('ruuvi_rx.subscribe')

ruuvi_rx = RuuviTagReactive()


def hadle_rx(found_data):
    print(found_data)
    ruuvi_rx.stop()
    if not found_data:
        raise Exception('FAILED')
    else:
        print('OK')

ruuvi_rx.get_subject().\
    subscribe(hadle_rx)

wait_for_finish(ruuvi_rx._run_flag, 'ruuvi_rx.subscribe')


print('Verification OK')
