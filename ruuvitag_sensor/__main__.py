import sys

from ruuvi import RuuviTagSensor

if __name__ == '__main__':
    mac = sys.argv[1]
    sensor = RuuviTagSensor(mac, 'test')
    state = sensor.update()
    print(state)
