import asyncio
import os
os.environ['RUUVI_BLE_ADAPTER'] = 'bleak'

from ruuvitag_sensor.ruuvi import RuuviTagSensor
import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()


async def main():
    data = await RuuviTagSensor.get_first_raw_data_async('FE:52:F7:B3:65:CC')
    print(data)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
