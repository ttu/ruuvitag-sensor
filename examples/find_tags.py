'''
Find RuuviTags
'''

from ruuvitag_sensing.ruuvi import RuuviTagSensor
import ruuvitag_sensing.log

ruuvitag_sensing.log.enable_console()

# This will print sensor's mac and state when new sensor is found
RuuviTagSensor.find_ruuvitags()
