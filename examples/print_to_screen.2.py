'''
Printing Data to Shell Window
Press Ctrl+C to escape running sequence
'''

from ruuvitag_sensing.testing import MyRuuvi

mac = 'E8:C7:D7:F2:4B:47'
sleepTime = 0

ruuvi_sensor = MyRuuvi(mac)
ruuvi_sensor.print_data(sleepTime)
