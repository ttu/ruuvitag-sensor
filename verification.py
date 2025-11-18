"""
Verification script for RuuviTags. Requires at least one active RuuviTag.
"""

import time

from ruuvitag_sensor.decoder import Df3Decoder, UrlDecoder
from ruuvitag_sensor.ruuvi import RunFlag, RuuviTagSensor
from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive
from ruuvitag_sensor.ruuvitag import RuuviTag

# Uncomment to turn on console print
# import ruuvitag_sensor
# from ruuvitag_sensor.log import log
# ruuvitag_sensor.log.enable_console()


#
# Helper Functions
#
def print_header(name):
    print("############################################")
    print(name)
    print("############################################")


def wait_for_finish(run_flag, name):
    max_time = 20

    while run_flag.running:
        time.sleep(0.1)
        max_time -= 0.1
        if max_time < 0:
            raise Exception(f"{name} not finished")


#
# UrlDecoder.decode_data
#
print_header("UrlDecoder.decode_data")

url_decoder = UrlDecoder()
url_data = url_decoder.decode_data("AjwYAMFc")
print(url_data)

if not url_data or not url_data["temperature"]:
    raise Exception("FAILED")

print("OK")


#
# UrlDecoder.decode_data
#
print_header("UrlDecoder.decode_data")

df3_decoder = Df3Decoder()
df3_data = df3_decoder.decode_data("03291A1ECE1EFC18F94202CA0B5300000000BB")
print(df3_data)

if not df3_data or not df3_data["temperature"]:
    raise Exception("FAILED")

print("OK")


#
# RuuviTagSensor.get_data_for_sensors
#
print_header("RuuviTagSensor.get_data_for_sensors")

data_for_sensors = RuuviTagSensor.get_data_for_sensors(search_duration_sec=15)
print(data_for_sensors)

if not data_for_sensors:
    raise Exception("FAILED")

print("OK")


#
# RuuviTagSensor.get_data_for_sensors with macs
#
print_header("RuuviTagSensor.get_data_for_sensors with macs")

macs = list(data_for_sensors.keys())
data_with_macs = RuuviTagSensor.get_data_for_sensors(macs, search_duration_sec=15)
print(data_with_macs)

if not data_with_macs:
    raise Exception("FAILED")

print("OK")


#
# RuuviTag.update
#
print_header("RuuviTag.update")

tag = RuuviTag(macs[0])
tag.update()
print(tag.state)

if not tag.state:
    raise Exception("FAILED")

print("OK")


#
# RuuviTagSensor.get_data
#
print_header("RuuviTagSensor.get_data")

flag = RunFlag()


def handle_data(found_data):
    flag.running = False
    if not found_data:
        raise Exception("FAILED")

    print("OK")


RuuviTagSensor.get_data(handle_data, run_flag=flag)

wait_for_finish(flag, "RuuviTagSensor.get_data")


#
# ruuvi_rx.subscribe
#
print_header("ruuvi_rx.subscribe")

ruuvi_rx = RuuviTagReactive()


def hadle_rx(found_data):
    print(found_data)
    ruuvi_rx.stop()
    if not found_data:
        raise Exception("FAILED")

    print("OK")


ruuvi_rx.get_subject().subscribe(hadle_rx)

wait_for_finish(ruuvi_rx._run_flag, "ruuvi_rx.subscribe")


print("Verification OK")
