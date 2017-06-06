'''
Find RuuviTags
'''

from ruuvitag_sensor.ruuvi import RuuviTagSensor
import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()

# This will print sensor's mac and state when new sensor is found
RuuviTagSensor.find_ruuvitags()
