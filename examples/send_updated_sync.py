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

while True:
    datas = RuuviTagSensor.get_data_for_sensors([], 10)
    current_time = datetime.now()

    for key, value in datas.items():
        if key in all_data and all_data[key]['data'] == value:
            continue
        all_data[key] = {'mac': key, 'data': value, 'timestamp': current_time}

    new_data = {key: value for key, value in all_data.items() if value['timestamp'] is current_time}

    for mac, data in new_data.items():
        data_copy = copy.copy(data)
        data_copy['timestamp'] = current_time.isoformat()
        requests.put('{url}/sensors/{mac}'.format(url=server_url, mac=quote(mac)), json=data_copy)
        requests.post('{url}/sensordatas'.format(url=server_url), json=data_copy)

    not_found = [key for key, value in all_data.items() if value['timestamp'] < datetime.now() - timedelta(minutes=10)]
    for key in not_found:
        # TODO: Notify of lost sensors
        del all_data[key]
