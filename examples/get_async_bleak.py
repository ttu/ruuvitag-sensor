import asyncio

import os
os.environ['RUUVI_BLE_ADAPTER'] = 'Bleak'

from ruuvitag_sensor.ruuvi import RuuviTagSensor


def handle_data(found_data):
    print(found_data)
    # print('MAC ' + found_data[0])
    # print(found_data[1])

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(RuuviTagSensor.get_datas_async(handle_data))
