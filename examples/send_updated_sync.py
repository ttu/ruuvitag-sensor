"""
Get latest sensor data for all sensors every 10 seconds an keep track of current
states in own dictionary.
Send updated data synchronously to server with requests.

Example sends data (application/json) to:
    POST http://10.0.0.1:5000/api/sensordata
    PUT  http://10.0.0.1:5000/api/sensors/{mac}

Requires:
    Requests - pip install requests
"""

import copy
from datetime import datetime, timedelta
from urllib.parse import quote

import requests

from ruuvitag_sensor.ruuvi import RuuviTagSensor

all_data = {}
server_url = 'http://10.0.0.1:5000/api'


def handle_data(received_data):
    current_time = datetime.now()

    mac = received_data[0]
    value = received_data[1]

    all_data[mac] = {'mac': mac, 'data': value, 'timestamp': current_time}

    # NOTE: Sending should be done in background and not in the same callback.
    # Check send_updated_async.py.

    data_copy = copy.copy(all_data[mac])
    data_copy['timestamp'] = current_time.isoformat()
    requests.put(f'{server_url}/sensors/{quote(mac)}')
    requests.post(f'{server_url}/sensordata')

    not_found = [mac for mac, value in all_data.items()
                 if value['timestamp'] < datetime.now() - timedelta(minutes=10)]
    for mac in not_found:
        # TODO: Notify of lost sensors
        del all_data[mac]


RuuviTagSensor.get_data(handle_data)
