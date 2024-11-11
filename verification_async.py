"""
Verification script for RuuviTags. Requires at least one active RuuviTag.
"""

import asyncio
import logging
import sys

import ruuvitag_sensor
from ruuvitag_sensor.decoder import Df3Decoder, UrlDecoder
from ruuvitag_sensor.log import log
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive
from ruuvitag_sensor.ruuvitag import RuuviTagAsync

ruuvitag_sensor.log.enable_console()
log.setLevel(logging.DEBUG)
for handler in log.handlers:
    handler.setLevel(logging.DEBUG)


#
# Helper Functions
#
def print_header(name):
    print("############################################")
    print(name)
    print("############################################")


async def wait_for_finish(run_flag, name):
    max_time = 20

    while run_flag.running:
        await asyncio.sleep(0.1)
        max_time -= 0.1
        if max_time < 0:
            raise Exception(f"{name} not finished")


#
# UrlDecoder.decode_data
#
def test_url_decoder():
    print_header("UrlDecoder.decode_data")

    decoder = UrlDecoder()
    url_decoded_data = decoder.decode_data("AjwYAMFc")
    print(url_decoded_data)

    if not url_decoded_data["temperature"]:
        raise Exception("FAILED")

    print("OK")


#
# Df3Decoder.decode_data
#
def test_df3_decoder():
    print_header("Df3Decoder.decode_data")

    decoder = Df3Decoder()
    df3_decoded_data = decoder.decode_data("03291A1ECE1EFC18F94202CA0B5300000000BB")
    print(df3_decoded_data)

    if not df3_decoded_data["temperature"]:
        raise Exception("FAILED")

    print("OK")


async def test_get_data_for_sensors_async() -> list[str]:
    #
    # RuuviTagSensor.get_data_for_sensors_async
    #
    print_header("RuuviTagSensor.get_data_for_sensors_async")

    data = await RuuviTagSensor.get_data_for_sensors_async(search_duration_sec=5)
    print(data)

    if not data:
        raise Exception("FAILED")

    print("OK")
    return next(iter(data.keys()))


async def test_get_data_for_sensors_async_with_macs(mac: list[str]):
    #
    # RuuviTagSensor.get_data_for_sensors with macs
    #
    print_header("RuuviTagSensor.get_data_for_sensors with macs")

    data = await RuuviTagSensor.get_data_for_sensors_async(mac, search_duration_sec=5)
    print(data)

    if not data:
        raise Exception("FAILED")

    print("OK")


async def test_ruuvitagasync_update(mac: list[str]):
    #
    # RuuviTagAsync.update
    #
    print_header("RuuviTagAsync.update")

    tag = RuuviTagAsync(mac)
    await tag.update()
    print(tag.state)

    if not tag.state:
        raise Exception("FAILED")

    print("OK")


async def test_get_data_async():
    #
    # RuuviTagSensor.get_data_async
    #
    print_header("RuuviTagSensor.get_data_async")

    # TODO: throw exception after 15 seconds

    async for data in RuuviTagSensor.get_data_async():
        break

    print("OK")


async def test_ruuvi_rx():
    #
    # RuuviTagReactive.subscribe
    #
    print_header("RuuviTagReactive.subscribe")

    ruuvi_rx = RuuviTagReactive()

    def handle_rx(found_data):
        print(found_data)
        ruuvi_rx.stop()
        if not found_data:
            raise Exception("FAILED")

        print("OK")

    ruuvi_rx.get_subject().subscribe(handle_rx)

    await wait_for_finish(ruuvi_rx._run_flag, "ruuvi_rx.subscribe")


async def main():
    test_url_decoder()
    test_df3_decoder()
    mac = await test_get_data_for_sensors_async()
    await test_get_data_for_sensors_async_with_macs(mac)
    if not sys.platform.startswith("darwin"):
        await test_ruuvitagasync_update(mac)
    await test_ruuvi_rx()
    print("Verification OK")


if __name__ == "__main__":
    asyncio.run(main())
