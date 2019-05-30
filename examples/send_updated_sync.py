'''
Get latest sensor data for all sensors every 10 seconds an keep track of current states in own dictionary.
Send updated data synchronously to server with requests.

Example sends data (application/json) to:
    POST http://10.0.0.1:5000/api/sensordatas
    PUT  http://10.0.0.1:5000/api/sensors/{mac}

Requires:
    Requests - pip install requests
'''

from urllib.parse import quote
from datetime import datetime, timedelta
import copy
import requests

from ruuvitag_sensor.ruuvi import RuuviTagSensor


all_data = {}
server_url = 'http://10.0.0.1:5000/api'


def handle_data(received_data):
    current_time = datetime.now()

    mac = received_data[0]
    value = received_data[1]

    all_data[mac] = {'mac': mac, 'data': value, 'timestamp': current_time}

    # NOTE: Sending should be done in background and not in the same callback. Check send_updated_async.py

    data_copy = copy.copy(all_data[mac])
    data_copy['timestamp'] = current_time.isoformat()
    requests.put('{url}/sensors/{mac}'.format(url=server_url, mac=quote(mac)), json=data_copy)
    requests.post('{url}/sensordatas'.format(url=server_url), json=data_copy)

    not_found = [mac for mac, value in all_data.items() if value['timestamp'] < datetime.now() - timedelta(minutes=10)]
    for mac in not_found:
        # TODO: Notify of lost sensors
        del all_data[mac]


RuuviTagSensor.get_datas(handle_data)
