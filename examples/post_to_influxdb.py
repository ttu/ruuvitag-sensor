'''
Get data from sensors and write it to InfluxDB

Requires:
    influxdb - pip install influxdb


** Docker InfluxDB & Grafana guide **

Download container
$ docker pull samuelebistoletti/docker-statsd-influxdb-grafana

Create and start new container
$ docker run -d --name docker-statsd-influxdb-grafana -p 3003:3003 -p 3004:8083 -p 8086:8086 -p 22022:22 -p 8125:8125/udp samuelebistoletti/docker-statsd-influxdb-grafana:latest

Or start existing container
$ docker start docker-statsd-influxdb-grafana

InfluxDB: http://localhost:3004/

First create new table: CREATE TABLE tag_data
Query to return all tag data: SELECT * FROM ruuvitag
Remove all data: DROP SERIES FROM ruuvitag

Grafana: http://localhost:3003/ (root/root)

Add datasource (type: InfluxDB url: http://localhost:8086, database: tag_data)
Add new graph to dashboard
'''

from influxdb import InfluxDBClient
from ruuvitag_sensor.ruuvi import RuuviTagSensor


def convert_to_influx(mac, payload):
    '''
    Convert data into RuuviCollecor naming schme and scale

    returns:
        Object to be written to InfluxDB
    '''
    fields = {}
    fields["temperature"]               = payload["temperature"] if ('temperature' in payload) else None
    fields["humidity"]                  = payload["humidity"] if ('humidity' in payload) else None
    fields["pressure"]                  = payload["pressure"] if ('pressure' in payload) else None
    fields["accelerationX"]             = payload["acceleration_x"] if ('acceleration_x' in payload) else None
    fields["accelerationY"]             = payload["acceleration_y"] if ('acceleration_y' in payload) else None
    fields["accelerationZ"]             = payload["acceleration_z"] if ('acceleration_z' in payload) else None
    fields["batteryVoltage"]            = payload["battery"]/1000.0 if hasattr(payload, 'battery') else None
    fields["dataFormat"]                = payload["data_format"] if ('data_format' in payload) else None
    fields["txPower"]                   = payload["tx_power"] if ('tx_power' in payload) else None
    fields["movementCounter"]           = payload["battery"] if ('battery' in payload) else None
    fields["measurementSequenceNumber"] = payload["measurement_sequence_number"] if ('measurement_sequence_number' in payload) else None
    fields["tagID"]                     = payload["tagID"] if ('tagID' in payload) else None
    return {
        "measurement": "ruuvi_measurements",
        "tags": {
            "mac": mac
        },
        "fields": fields
    }


client = InfluxDBClient(host="localhost", port=8086, database="ruuvi")

while True:
    datas = RuuviTagSensor.get_data_for_sensors()
    json_body = [convert_to_influx(mac, payload) for mac, payload in datas.items()]
    client.write_points(json_body)
