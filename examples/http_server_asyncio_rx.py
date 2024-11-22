"""
Simple http server, that returns data in json.
Executes get data for sensors in the background.

Endpoints:
    http://0.0.0.0:5000/data
    http://0.0.0.0:5000/data/{mac}

Requires:
    asyncio - Python 3.5
    aiohttp - pip install aiohttp
"""

import asyncio
from multiprocessing import Manager

from aiohttp import web
from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive


tags: dict[str, str] = {
    # "F4:A5:74:89:16:57": "kitchen",
    # "CC:2C:6A:1E:59:3D": "bedroom",
    # "BB:2C:6A:1E:59:3D": "livingroom",
}


async def get_all_data(_, shared_data):
    return web.json_response(dict(shared_data))


async def get_data(request, shared_data):
    mac = request.match_info.get("mac")
    if mac not in shared_data:
        return web.json_response(status=404)
    return web.json_response(dict(shared_data[mac]))


async def run_get_data_background(known_tags, shared_data):
    """
    Background process from RuuviTag Sensors
    """

    def handle_new_data(data):
        mac, sensor_data = data
        sensor_data["name"] = known_tags.get(mac, "unknown")
        shared_data[data[0]] = sensor_data

    ruuvi_rx = RuuviTagReactive(list(known_tags.keys()))
    data_stream = ruuvi_rx.get_subject()
    data_stream.subscribe(handle_new_data)


def setup_routes(application, shared_data):
    application.router.add_get("/data", lambda request: get_all_data(request, shared_data))
    application.router.add_get("/data/{mac}", lambda request: get_data(request, shared_data))


if __name__ == "__main__":
    m = Manager()
    data = m.dict()

    async def start_background_tasks(application):
        application["run_get_data"] = asyncio.create_task(run_get_data_background(tags, data))

    async def cleanup_background_tasks(application):
        application["run_get_data"].cancel()
        await asyncio.gather(app["run_get_data"], return_exceptions=True)
        print("Background tasks shut down.")

    # Setup and start web application
    app = web.Application()
    setup_routes(app, data)
    app.on_startup.append(start_background_tasks)
    app.on_shutdown.append(cleanup_background_tasks)
    web.run_app(app, host="0.0.0.0", port=5500)
