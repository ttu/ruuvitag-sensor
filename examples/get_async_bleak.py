import asyncio
import logging

import os
from ruuvitag_sensor.log import enable_console
os.environ['RUUVI_BLE_ADAPTER'] = 'Bleak'

from ruuvitag_sensor.ruuvi import RuuviTagSensor

enable_console()

log = logging.getLogger(__name__)

def handle_data(found_data):
    log.info(found_data)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(RuuviTagSensor.get_datas_async(handle_data))
