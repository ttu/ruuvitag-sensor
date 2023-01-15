"""
Simple http server, that returns data in json.
Executes get data for sensors in the background.

Endpoints:
    http://0.0.0.0:5000/data
    http://0.0.0.0:5000/data/<mac>

Requires:
    Flask - pip install flask
"""

import json
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from multiprocessing import Manager

from flask import Flask, abort

from ruuvitag_sensor.ruuvi import RuuviTagSensor

app = Flask(__name__)

all_data = {}

tags = {'F4:A5:74:89:16:57': 'kitchen', 'CC:2C:6A:1E:59:3D': 'bedroom', 'BB:2C:6A:1E:59:3D': 'livingroom'}


def run_get_data_background(macs, queue):
    """
    Background process from RuuviTag Sensors
    """

    def callback(data):
        data[1]['time'] = str(datetime.now())
        queue.put(data)

    RuuviTagSensor.get_data(callback, macs)


def update_data():
    """
    Update data sent by background process to global all_data
    """
    global all_data  # pylint: disable=global-variable-not-assigned
    while not q.empty():
        data = q.get()
        all_data[data[0]] = data[1]
    for key, value in tags.items():
        if key in all_data:
            all_data[key]['name'] = value


@app.route('/data')
def get_all_data():
    update_data()
    return json.dumps(all_data)


@app.route('/data/<mac>')
def get_data(mac):
    update_data()
    if mac not in all_data:
        abort(404)
    return json.dumps(all_data[mac])


if __name__ == '__main__':
    m = Manager()
    q = m.Queue()

    # Start background process
    executor = ProcessPoolExecutor(1)
    executor.submit(run_get_data_background, list(tags.keys()), q)

    # Strt Flask application
    app.run(host='0.0.0.0', port=5000)
