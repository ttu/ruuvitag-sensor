'''
Find RuuviTags
'''

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.log import configureLog

configureLog(True)

# This will print sensor's mac and state when new sensor is found
RuuviTagSensor.find_ruuvitags()
