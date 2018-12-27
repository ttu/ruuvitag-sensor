'''
Print sensor data to the screen. Update interval 1 sec.
Press Ctrl+C to quit.
'''

import time
import os
import math

from datetime import datetime
from ruuvitag_sensor.ruuvitag import RuuviTag

# Starting Routines
os.system('clear')
print('Starting')

# Change here your own device's mac-address
mac = 'E8:C7:D7:F2:4B:47'
sensor = RuuviTag(mac)
txPower = -59  # dBm
length = 30

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
    # Get "Ebenen-Neigung"
    norm_z = data['acceleration_z'] / data['acceleration']
    norm_x = data['acceleration_x'] / data['acceleration']
    norm_y = data['acceleration_y'] / data['acceleration']
    # Cos
    line_cosx = str.format('Elevation X:\t{0:.2f} °', math.acos(norm_x) * 180 / math.pi)
    line_cosy = str.format('Elevation Y:\t{0:.2f} °', math.acos(norm_y) * 180 / math.pi)
    line_cosz = str.format('Elevation Z:\t{0:.2f} °', math.acos(norm_z) * 180 / math.pi)
    # Sin
    line_sinx = str.format('Elevation X`:\t{0:.2f} °', math.asin(norm_x) * 180 / math.pi)
    line_siny = str.format('Elevation Y`:\t{0:.2f} °', math.asin(norm_y) * 180 / math.pi)
    line_sinz = str.format('Elevation Z`:\t{0:.2f} °', math.asin(norm_z) * 180 / math.pi)

    # --------------
    # Get Distance
    rssi = data['rssi']
    distance = (0.89976) * math.pow(rssi / txPower, 7.7095)+0.111
    if rssi/txPower <= 1:
        line_distance = str.format("Distance:\t{0:.1f} cm", distance / 100)
    else:
        line_distance = str.format("Distance:\t{0:.1f} m", distance)

    # --------------
    # Clear screen and print sensor data
    os.system('clear')
    print('Press Ctrl+C to quit.\n\r')
    print(str(datetime.now()))
    print(line_sen)
    print(line_bat)
    print(line_rssi)
    print(line_distance)
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
    print('Alle Winkel bzgl. XY-Ebene')
    print(line_cosx)
    print(line_cosy)
    print(line_cosz)
    print('-' * length)
    print('Alle Winkel bzgl. XZ/YZ-Ebene')
    print(line_sinx)
    print(line_siny)
    print(line_sinz)
    print('-' * length)

    try:
        # Wait and start over again
        time.sleep(0.45)
    except KeyboardInterrupt:
        # When Ctrl+C is pressed
        # execution of the while loop is stopped
        print('Exit')
        break
