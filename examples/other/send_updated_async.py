'''
Get latest sensor data for all sensors and keep track of current states in own dictionary.
Send updated data asynchronously to server with aiohttp.

Example sends data (application/json) to:
    POST http://10.0.0.1:5000/api/sensordatas
    PUT  http://10.0.0.1:5000/api/sensors/{mac}

Requires:
    asyncio - Python 3.5
    aiohttp - pip install aiohttp
'''

from datetime import datetime
from multiprocessing import Manager
from urllib.parse import quote
import json
from concurrent.futures import ProcessPoolExecutor
import asyncio
from aiohttp import ClientSession

from ruuvitag_sensor.ruuvi import RuuviTagSensor


all_data = {}
server_url = 'http://10.0.0.1:5000/api'


async def handle_queue(queue):

    async def send_post(session, update_data):
        async with session.post(
            '{url}/sensordatas'.format(url=server_url),
            data=json.dumps(update_data),
            headers={'content-type': 'application/json'}
        ) as response:
            response = await response.read()

    async def send_put(session, update_data):
        async with session.put(
            '{url}/sensors/{mac}'.format(url=server_url, mac=quote(update_data['mac'])),
            data=json.dumps(update_data),
            headers={'content-type': 'application/json'}
        ) as response:
            response = await response.read()

    async with ClientSession() as session:
        while True:
            if not queue.empty():
                funcs = []
                while not queue.empty():
                    update_data = queue.get()
                    funcs.append(send_put(session, update_data))
                    funcs.append(send_post(session, update_data))
                    if len(funcs) == 50:
                        continue
                if funcs:
                    await asyncio.wait(funcs)
            else:
                await asyncio.sleep(0.2)


def run_get_datas_background(queue):

    def handle_new_data(new_data):
        current_time = datetime.now()
        sensor_mac = new_data[0]
        sensor_data = new_data[1]

        if sensor_mac not in all_data or all_data[sensor_mac]['data'] != sensor_data:
            update_data = {'mac': sensor_mac, 'data': sensor_data, 'timestamp': current_time.isoformat()}
            all_data[sensor_mac] = update_data
            queue.put(update_data)

    RuuviTagSensor.get_datas(handle_new_data)


m = Manager()
q = m.Queue()

executor = ProcessPoolExecutor()
executor.submit(run_get_datas_background, q)

loop = asyncio.get_event_loop()
loop.run_until_complete(handle_queue(q))
