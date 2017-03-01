'''
Get all BLE device broadcasts
'''

from ruuvitag_sensor.ble_communication import BleCommunicationNix

ble = BleCommunicationNix()

for ble_data in ble.get_datas():
    print(ble_data)
