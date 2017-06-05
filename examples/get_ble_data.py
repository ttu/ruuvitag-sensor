'''
Get all BLE device broadcasts
'''

from ruuvitag_sensor.ble_communication import BleCommunicationNix
from ruuvitag_sensor.log import configureLog

configureLog(True)

ble = BleCommunicationNix()

for ble_data in ble.get_datas():
    print(ble_data)
