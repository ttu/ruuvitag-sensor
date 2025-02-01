import asyncio
from datetime import datetime, timedelta

import ruuvitag_sensor.log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console(10)


async def main():
    # On macOS, the device address is not a MAC address, but a system specific ID
    # mac = "CA:F7:44:DE:EB:E1"
    mac = "873A13F5-ED14-AEE1-E446-6ACF31649A1D"
    start_time = datetime.now() - timedelta(minutes=60)
    async for data in RuuviTagSensor.get_history_async(mac, start_time=start_time):
        print(data)


if __name__ == "__main__":
    asyncio.run(main())
