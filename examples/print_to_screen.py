"""
Print sensor data to the screen.

Press Ctrl+C to quit.

2017-02-02 13:45:25.233400
Sensor - F4:A5:74:89:16:57
Temperature: 10
Humidity:    28
Pressure:    689
"""

import os
from datetime import datetime

from ruuvitag_sensor.ruuvi import RuuviTagSensor

# Change here your own device's mac-address
mac = 'F4:A5:74:89:16:57'

print('Starting')

def print_data(received_data):
    received_mac = received_data[0]
    data = received_data[1]

    line_sen = str.format('Sensor - {0}', received_mac)
    line_tem = str.format('Temperature: {0} C', data['temperature'])
    line_hum = str.format('Humidity:    {0}', data['humidity'])
    line_pre = str.format('Pressure:    {0}', data['pressure'])

    # Clear screen and print sensor data
    os.system('clear')
    print('Press Ctrl+C to quit.\n\r\n\r')
    print(str(datetime.now()))
    print(line_sen)
    print(line_tem)
    print(line_hum)
    print(line_pre)
    print('\n\r\n\r.......')


RuuviTagSensor.get_datas(print_data, mac)
