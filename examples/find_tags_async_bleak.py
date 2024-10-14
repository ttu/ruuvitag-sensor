"""
Asynchronous find RuuviTags
"""

import asyncio

import ruuvitag_sensor.log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()


async def main():
    await RuuviTagSensor.find_ruuvitags_async()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
