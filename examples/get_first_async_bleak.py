import asyncio
import os

os.environ["RUUVI_BLE_ADAPTER"] = "bleak"

import ruuvitag_sensor.log
from ruuvitag_sensor.decoder import Df5Decoder
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()


async def main():
    """
    NOTE: This is for example use of get_first_raw_data_async. Normally use get_data_async-method.

    async for data in RuuviTagSensor.get_data_async(['FA:52:F7:B3:65:CC']):
        print(data)
    """
    data = await RuuviTagSensor.get_first_raw_data_async("FA:52:F7:B3:65:CC")
    print(f"Raw: {data}")
    decoded = Df5Decoder().decode_data(data[1])
    print(f"Decoded: {decoded}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
