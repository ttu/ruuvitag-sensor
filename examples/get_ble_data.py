"""
Get all BLE device broadcasts
"""

from ruuvitag_sensor.adaptors.nix_hci import BleCommunicationNix
import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()

ble = BleCommunicationNix()

for ble_data in ble.get_datas():
    print(ble_data)
