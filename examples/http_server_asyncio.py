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

import asyncio
from multiprocessing import Queue
from concurrent.futures import ThreadPoolExecutor
from aiohttp import web
from ruuvitag_sensor.ruuvi import RuuviTagSensor

q = Queue()

allData = {}

tags = {
    'F4:A5:74:89:16:57': 'kitchen',
    'CC:2C:6A:1E:59:3D': 'bedroom',
    'BB:2C:6A:1E:59:3D': 'livingroom'
}

timeout_in_sec = 5


def run_get_data_background(macs, queue):
    """
    Background process from RuuviTag Sensors
    """
    while True:
        datas = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)
        queue.put(datas)


async def data_update():
    """
    Update data sent by the background process to global allData variable
    """
    global allData
    while True:
        while not q.empty():
            allData = q.get()
        for key, value in tags.items():
            if key in allData:
                allData[key]['name'] = value
        await asyncio.sleep(timeout_in_sec)


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
    # Start background process
    executor = ThreadPoolExecutor(1)
    executor.submit(run_get_data_background, list(tags.keys()), q)

    loop = asyncio.get_event_loop()

    # Start data updater
    loop.create_task(data_update())

    # Setup and start web application
    app = web.Application(loop=loop)
    setup_routes(app)
    web.run_app(app, host='0.0.0.0', port=5000)
