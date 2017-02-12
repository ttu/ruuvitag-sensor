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
from multiprocessing import Queue
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, abort
from ruuvitag_sensor.ruuvi import RuuviTagSensor

app = Flask(__name__)

q = Queue()

allData = {}

tags = {
    'F4:A5:74:89:16:57': 'kitchen',
    'CC:2C:6A:1E:59:3D': 'bedroom',
    'BB:2C:6A:1E:59:3D': 'livingroom'
}


def run_get_data_background(macs, queue):
    while True:
        timeout_in_sec = 5
        datas = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)
        q.put(datas)


executor = ThreadPoolExecutor(1)
executor.submit(run_get_data_background, list(tags.keys()), q)


def update_data():
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
    app.run(host='0.0.0.0', port=5000)
