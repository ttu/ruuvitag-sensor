import asyncio
import os

os.environ["RUUVI_BLE_ADAPTER"] = "bleak"

import ruuvitag_sensor.log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()


async def main():
    async for data in RuuviTagSensor.get_data_async():
        print(data)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
