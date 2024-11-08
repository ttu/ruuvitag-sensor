"""
Find RuuviTags
"""

import os

os.environ["RUUVI_BLE_ADAPTER"] = "bluez"

import ruuvitag_sensor.log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()

# This will print sensor's mac and state when new sensor is found
if __name__ == "__main__":
    RuuviTagSensor.find_ruuvitags()
