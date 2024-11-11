"""
Asynchronously find RuuviTags
"""

import asyncio

import ruuvitag_sensor.log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()


async def main():
    try:
        await RuuviTagSensor.find_ruuvitags_async()
    except asyncio.exceptions.CancelledError:
        print("Scan stopped")


if __name__ == "__main__":
    asyncio.run(main())
