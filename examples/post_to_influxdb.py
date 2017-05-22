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
from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive

client = InfluxDBClient(host="localhost", port=8086, database="tag_data")

tags = {
    'FE:52:F7:B3:65:CC': 'kitchen',
    'CA:F7:44:DE:EB:E1': 'bedroom',
    'BB:2C:6A:1E:59:3D': 'livingroom'
}


def write_to_influxdb(received_data):
    json_body = [
        {
            "measurement": "ruuvitag",
            "tags": {
                "mac": received_data[0]
            },
            "fields": {
                "temperature": received_data[1]["temperature"],
                "humidity": received_data[1]["humidity"],
                "pressure": received_data[1]["pressure"]
            }
        }
    ]

    client.write_points(json_body)

ruuvi_rx = RuuviTagReactive(list(tags.keys()))

# Write data to InfluxDB from every tag every 5 sec
ruuvi_rx.get_subject().\
    group_by(lambda x: x[0]).\
    subscribe(lambda x: x.sample(5000).subscribe(write_to_influxdb))
