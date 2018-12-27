'''
Get all BLE device broadcasts
'''

from ruuvitag_sensing.ble_communication import BleCommunicationNix
import ruuvitag_sensing.log

ruuvitag_sensing.log.enable_console()

ble = BleCommunicationNix()

for ble_data in ble.get_datas():
    print(ble_data)
