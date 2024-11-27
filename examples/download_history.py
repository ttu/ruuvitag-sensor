import asyncio

import ruuvitag_sensor.log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()


async def main():
    # On macOS, the device address is not a MAC address, but a system specific ID
    # mac = "CA:F7:44:DE:EB:E1"
    mac = "873A13F5-ED14-AEE1-E446-6ACF31649A1D"
    data = await RuuviTagSensor.download_history(mac)
    print(data)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
