'''
Simple http server, that returns data in json.
Executes get data for sensors in the background.

Endpoints:
    http://0.0.0.0:5000/data
    http://0.0.0.0:5000/data/<mac>

Requires:
    Flask - pip install flask
'''

import json
from multiprocessing import Manager
from concurrent.futures import ProcessPoolExecutor
from flask import Flask, abort
from ruuvitag_sensor.ruuvi import RuuviTagSensor

app = Flask(__name__)

m = Manager()
q = m.Queue()

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


def update_data():
    """
    Update data sent by background process to global allData
    """
    global allData
    while not q.empty():
        allData = q.get()
    for key, value in tags.items():
        if key in allData:
            allData[key]['name'] = value


@app.route('/data')
def get_all_data():
    update_data()
    return json.dumps(allData)


@app.route('/data/<mac>')
def get_data(mac):
    update_data()
    if mac not in allData:
        abort(404)
    return json.dumps(allData[mac])


if __name__ == '__main__':
    # Start background process
    executor = ProcessPoolExecutor(1)
    executor.submit(run_get_data_background, list(tags.keys()), q)

    # Strt Flask application
    app.run(host='0.0.0.0', port=5000)
