"""
Get data from sensors and write it to InfluxDB

Requires:
    influxdb - pip install influxdb


** Docker InfluxDB & Grafana guide **

Download container
$ docker pull samuelebistoletti/docker-statsd-influxdb-grafana

Create and start new container
$ docker run -d --name docker-statsd-influxdb-grafana -p 3003:3003 -p 3004:8083 -p 8086:8086 \
 -p 22022:22 -p 8125:8125/udp samuelebistoletti/docker-statsd-influxdb-grafana:latest

Or start existing container
$ docker start docker-statsd-influxdb-grafana

InfluxDB: http://localhost:3004/

First create new database: CREATE DATABASE ruuvi
Query to return all tag data: SELECT * FROM ruuvi_measurements
Remove all data: DROP SERIES FROM ruuvi_measurements

Grafana: http://localhost:3003/ (root/root)

Add datasource (type: InfluxDB url: http://localhost:8086, database: ruuvi)
Add new graph to dashboard
"""

import os

from influxdb import InfluxDBClient

os.environ["RUUVI_BLE_ADAPTER"] = "bluez"

from ruuvitag_sensor.ruuvi import RuuviTagSensor

client = InfluxDBClient(host="localhost", port=8086, database="ruuvi")


def write_to_influxdb(received_data):
    """
    Convert data into RuuviCollector naming scheme and scale

    returns:
        Object to be written to InfluxDB
    """
    mac = received_data[0]
    payload = received_data[1]

    dataFormat = payload.get("data_format", None)
    fields = {}
    fields["temperature"] = payload.get("temperature", None)
    fields["humidity"] = payload.get("humidity", None)
    fields["pressure"] = payload.get("pressure", None)
    fields["accelerationX"] = payload.get("acceleration_x", None)
    fields["accelerationY"] = payload.get("acceleration_y", None)
    fields["accelerationZ"] = payload.get("acceleration_z", None)
    fields["batteryVoltage"] = payload["battery"] / 1000.0 if ("battery" in payload) else None
    fields["txPower"] = payload.get("tx_power", None)
    fields["movementCounter"] = payload.get("movement_counter", None)
    fields["measurementSequenceNumber"] = payload.get("measurement_sequence_number", None)
    fields["tagID"] = payload.get("tagID", None)
    fields["rssi"] = payload.get("rssi", None)
    json_body = [
        {"measurement": "ruuvi_measurements", "tags": {"mac": mac, "dataFormat": dataFormat}, "fields": fields}
    ]
    client.write_points(json_body)


if __name__ == "__main__":
    RuuviTagSensor.get_data(write_to_influxdb)
