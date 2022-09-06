import asyncio
import os
os.environ['RUUVI_BLE_ADAPTER'] = 'bleak'

from ruuvitag_sensor.ruuvi import RuuviTagSensor
import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()


async def main():
    async for data in RuuviTagSensor.get_data_async():
        print(data)

if __name__ == '__main__':
    asyncio.run(main())
