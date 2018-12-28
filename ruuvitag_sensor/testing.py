'''
Class included in ruuvitag_sensor for
printing data extracted from RuuviTag Raw Data Format (v1,v2)
- is df3 and df5 - in shell.
'''

import os
import math

from datetime import datetime

class MyRuuvi():
    from ruuvitag_sensor.ruuvitag import RuuviTag

    def __init__(self, mac_addr='E8:C7:D7:F2:4B:47', bt_device=''):
        self._sensor = RuuviTag(mac_addr, bt_device)
        self._data_count = 0

    ### Properties ###
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
    def dataformat(self):
        return self.state['data_format']

    @property
    def elev_x(self):
        return math.acos(self.acc_x / self.acc) * 180 / math.pi

    @property
    def elev_y(self):
        return math.acos(self.acc_y / self.acc) * 180 / math.pi

    @property
    def elev_z(self):
        return math.acos(self.acc_z / self.acc) * 180 / math.pi

    @property
    def rssi(self):
        return self.state['rssi']

    @property
    def data_count(self):
        return self._data_count

    ### Methods ###
    def update(self):
        self._sensor.update()
        self._data_count += 1

    def print_to_shell(self, running=True):
        '''
        Printing collected/extracted data to shell
        '''
        if not running:
            return

        # Starting routines
        if self.data_count == 0:
            os.system('clear')
            print('Starting...\nPrinting Data to shell')

        self.update()
        os.system('clear')
        print('Press Ctr+C to quit.\n\r')
        print(str(datetime.now()))
        print('Sensor:\t{}'.format(self.mac))
        print('-'*30)
        print('Temperature:\t{:.2f}\t°C'.format(self.temp))
        print('Humidity:\t{:.2f}\t%'.format(self.humid))
        print('Pressure:\t{:.2f}\thPa'.format(self.press))
        print('-'*30)
        print('Acceleration:\t{:.0f}\tmG'.format(self.acc))
        print('X:\t\t{:.0f}\tmG'.format(self.acc_x))
        print('Y:\t\t{:.0f}\tmG'.format(self.acc_y))
        print('Z:\t\t{:.0f}\tmG'.format(self.acc_z))
        print('-'*30)
        print('Elevation X:\t{:.0f}\t°'.format(self.elev_x))
        print('Elevation Y:\t{:.0f}\t°'.format(self.elev_y))
        print('Elevation Z:\t{:.0f}\t°'.format(self.elev_z))
        print('-' * 30)
        print('RSSI:\t\t{}\tdBm'.format(self.rssi))
        print('Battery:\t{:.0f}\tmV'.format(self.bat))
        print('Data Count:\t{}'.format(self.data_count))
