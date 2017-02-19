'''
Simple http server, that returns data in json.
Executes get data for sensors in the background.

Endpoints:
    http://0.0.0.0:5000/data
    http://0.0.0.0:5000/data/{mac}

Requires:
    asyncio - Python 3.5
    aiohttp - pip install aiohttp
'''

from datetime import datetime
import asyncio
from multiprocessing import Manager
from concurrent.futures import ProcessPoolExecutor
from aiohttp import web
from ruuvitag_sensor.ruuvi import RuuviTagSensor

allData = {}


def run_get_data_background(macs, queue):
    """
    Background process from RuuviTag Sensors
    """

    def callback(data):
        data[1]['time'] = str(datetime.now())
        queue.put(data)

    RuuviTagSensor.get_datas(callback, macs)


async def data_update(queue):
    """
    Update data sent by the background process to global allData variable
    """
    global allData
    while True:
        while not queue.empty():
            data = queue.get()
            allData[data[0]] = data[1]
        for key, value in tags.items():
            if key in allData:
                allData[key]['name'] = value
        await asyncio.sleep(0.5)


async def get_all_data(request):
    return web.json_response(allData)


async def get_data(request):
    mac = request.match_info.get("mac")
    if mac not in allData:
        return web.json_response(status=404)
    return web.json_response(allData[mac])


def setup_routes(app):
    app.router.add_get('/data', get_all_data)
    app.router.add_get('/data/{mac}', get_data)


if __name__ == '__main__':
    tags = {
        'F4:A5:74:89:16:57': 'kitchen',
        'CC:2C:6A:1E:59:3D': 'bedroom',
        'BB:2C:6A:1E:59:3D': 'livingroom'
    }

    m = Manager()
    q = m.Queue()

    # Start background process
    executor = ProcessPoolExecutor(1)
    executor.submit(run_get_data_background, list(tags.keys()), q)

    loop = asyncio.get_event_loop()

    # Start data updater
    loop.create_task(data_update(q))

    # Setup and start web application
    app = web.Application(loop=loop)
    setup_routes(app)
    web.run_app(app, host='0.0.0.0', port=5000)
