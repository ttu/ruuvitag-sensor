"""
Get all BLE device broadcasts
"""

import ruuvitag_sensor.log
from ruuvitag_sensor.adapters.nix_hci import BleCommunicationNix

ruuvitag_sensor.log.enable_console()

ble = BleCommunicationNix()

for ble_data in ble.get_data():
    print(ble_data)
