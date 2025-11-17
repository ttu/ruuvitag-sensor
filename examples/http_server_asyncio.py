"""
Simple http server, that returns data in json.
Executes get data for sensors in the background.

Endpoints:
    http://0.0.0.0:5500/data
    http://0.0.0.0:5500/data/{mac}

Requires:
    asyncio - Python 3.5
    aiohttp - pip install aiohttp
"""

import asyncio
from datetime import datetime, timezone
from multiprocessing import Manager
from multiprocessing.managers import DictProxy
from queue import Queue

from aiohttp import web

from ruuvitag_sensor.ruuvi import RuuviTagSensor

tags: dict[str, str] = {
    # "F4:A5:74:89:16:57": "kitchen",
    # "CC:2C:6A:1E:59:3D": "bedroom",
    # "BB:2C:6A:1E:59:3D": "livingroom",
}


async def run_get_data_background(macs_to_fetch: list[str], queue: Queue):
    """
    Background process from RuuviTag Sensors
    """
    async for sensor_data in RuuviTagSensor.get_data_async(macs_to_fetch):
        sensor_data[1]["time"] = str(datetime.now(timezone.utc))  # type: ignore
        queue.put(sensor_data)


async def data_update(queue: Queue, shared_data: DictProxy):
    """
    Update data sent by the background process to global all_data variable
    """
    while True:
        while not queue.empty():
            mac, sensor_data = queue.get()
            shared_data["name"] = tags.get(mac, "unknown")
            shared_data[mac] = sensor_data
        await asyncio.sleep(0.5)


async def get_all_data(_: web.Request, shared_data: DictProxy):
    return web.json_response(dict(shared_data))


async def get_data(request: web.Request, shared_data: DictProxy):
    mac = request.match_info.get("mac")
    if mac not in shared_data:
        return web.json_response(status=404)
    return web.json_response(dict(shared_data[mac]))


def setup_routes(application: web.Application, shared_data: DictProxy):
    application.router.add_get("/data", lambda request: get_all_data(request, shared_data))
    application.router.add_get("/data/{mac}", lambda request: get_data(request, shared_data))


if __name__ == "__main__":
    m = Manager()
    data: DictProxy = m.dict()
    q: Queue = m.Queue()

    macs = list(tags.keys())

    async def start_background_tasks(application: web.Application):
        application["run_get_data"] = asyncio.create_task(run_get_data_background(macs, q))
        application["data_updater"] = asyncio.create_task(data_update(q, data))

    async def cleanup_background_tasks(application: web.Application):
        application["run_get_data"].cancel()
        application["data_updater"].cancel()
        await asyncio.gather(app["run_get_data"], app["data_updater"], return_exceptions=True)
        print("Background tasks shut down.")

    # Setup and start web application
    app = web.Application()
    setup_routes(app, data)
    app.on_startup.append(start_background_tasks)
    app.on_shutdown.append(cleanup_background_tasks)
    web.run_app(app, host="0.0.0.0", port=5500)
