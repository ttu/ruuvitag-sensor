"""
Asynchronous find RuuviTags
"""

import asyncio
import os
os.environ['RUUVI_BLE_ADAPTER'] = 'bleak'

from ruuvitag_sensor.ruuvi import RuuviTagSensor
import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()


async def main():
    await RuuviTagSensor.find_ruuvitags_async()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
