'''
Testing new added RSSI Value
Extracted from BLE-Byte-Data
'''

import time
import os

from datetime import datetime
from ruuvitag_sensor.ruuvitag import RuuviTag

# Starting Routines
os.system('clear')
print('Starting')

# Change here your own device's mac-address
length = 30
mac = 'E8:C7:D7:F2:4B:47'
sensor = RuuviTag(mac)

while True:
    data = sensor.update()

    # --------------
    # Get general data
    line_sen = str.format('Sensor - {0}', mac)
    line_rssi = str.format('RSSI:\t\t{0:.0f} dBm', data['rssi'])
    line_bat = str.format('Battery:\t{0:.0f} mV', data['battery'])
    line_tem = str.format('Temperature:\t{0:.1f} °C', data['temperature'])
    line_hum = str.format('Humidity:\t{0:.1f} %', data['humidity'])
    line_pre = str.format('Pressure:\t{0:.1f} mbar', data['pressure'])
    line_acc = str.format('Acceleration:\t{0:4.2f}', data['acceleration'])
    line_accx = str.format('In X:\t\t{0:4.2f}', data['acceleration_x'])
    line_accy = str.format('In Y:\t\t{0:4.2f}', data['acceleration_y'])
    line_accz = str.format('In Z:\t\t{0:4.2f}', data['acceleration_z'])

    # --------------
    # Clear screen and print sensor data
    os.system('clear')
    print('Press Ctrl+C to quit.\n\r')
    print(str(datetime.now()))
    print(line_sen)
    print(line_bat)
    print(line_rssi)
    print('-' * length)
    print(line_tem)
    print(line_hum)
    print(line_pre)
    print('-' * length)
    print(line_acc)
    print(line_accx)
    print(line_accy)
    print(line_accz)
    print('-' * length)

    try:
        # Wait and start over again
        time.sleep(0.45)
    except KeyboardInterrupt:
        # When Ctrl+C is pressed
        # execution of the while loop is stopped
        print('Exit')
        break
