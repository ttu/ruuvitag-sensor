'''
Class included in ruuvitag_sensing for
printing data extracted from RuuviTag Raw Data Format (v1,v2)
- is df3 and df5 - in shell.
'''

import time
import os

from datetime import datetime
from ruuvitag_sensor.ruuvitag import RuuviTag

class MyRuuvi():

    def __init__(self, mac_addr, bt_device=''):
        self._sensor = RuuviTag(mac_addr, bt_device)

    @property
    def mac(self):
        return self._sensor.mac

    @property
    def state(self):
        return self._sensor.state

    @property
    def temp(self):
        return self.state['temperature']

    @property
    def humid(self):
        return self.state['humidity']

    @property
    def press(self):
        return self.state['pressure']

    @property
    def acc(self):
        return self.state['acceleration']

    @property
    def acc_x(self):
        return self.state['acceleration_x']

    @property
    def acc_y(self):
        return self.state['acceleration_y']

    @property
    def acc_z(self):
        return self.state['acceleration_z']

    @property
    def bat(self):
        return self.state['battery']

    @property
    def rssi(self):
        return self.state['rssi']

    def print_data(self, sleepTime=0.1, runFlag=True):
        ''' Printing Data '''
        # Starting routines
        os.system('clear')
        print('Starting...\nPrinting Data 2 Screen')

        while True and runFlag:
            try:
                self._sensor.update()
                os.system('clear')
                print('Press Ctr + C to quit.\n\r')
                print(str(datetime.now()))
                print('Sensor:\t{}'.format(self.mac))
                print('-'*30)
                print('Temperature:\t{:.2f}°C'.format(self.temp))
                print('Humidity:\t{:.1f}%'.format(self.humid))
                print('Pressure:\t{:.0f}hPa'.format(self.press))
                print('-'*30)
                print('Acceleration:\t{:0f} mG'.format(self.acc))
                print('X:\t\t{:0f} mG'.format(self.acc_x))
                print('Y:\t\t{:0f} mG'.format(self.acc_y))
                print('Z:\t\t{:0f} mG'.format(self.acc_z))
                print('-'*30)
                time.sleep(sleepTime)
            except KeyboardInterrupt:
                # When Ctrl+C is pressed
                # execution of the while loop is stopped
                print('Exit')
                break
