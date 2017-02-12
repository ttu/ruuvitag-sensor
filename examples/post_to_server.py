'''
Get data from sensors and post it to specified url in json-format

Requires:
    Requests - pip install requests
'''

from urllib.parse import quote
import requests
from ruuvitag_sensor.ruuvi import RuuviTagSensor

macs = [
    'F4:A5:74:89:16:57',
    'CC:2C:6A:1E:59:3D',
    'BB:2C:6A:1E:59:3D'
]

# This should be enough that we find at least one result for each
timeout_in_sec = 4

url = 'http://localhost:8000/data/'

datas = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)

# Use Requests to POST datas in json-format
# Encode mac as it contains semicolon, which is reserved character
for key, value in datas.items():
    # url e.g.: http://localhost:8000/data/F4%3AA5%3A74%3A89%3A16%3A57
    # json e.g.: {"temperature": 24.0, "humidity": 38.0, "pressure": 1018.0}
    requests.post(url + quote(key), json=value)
