import asyncio

import ruuvitag_sensor.log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()


async def main():
    try:
        async for data in RuuviTagSensor.get_data_async():
            print(data)
    except asyncio.exceptions.CancelledError:
        print("Scan stopped")


if __name__ == "__main__":
    asyncio.run(main())
