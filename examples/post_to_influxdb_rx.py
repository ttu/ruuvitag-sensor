"""
Get data for sensors using rx and write it to InfluxDB

Check guide and requirements from post_to_influxdb.py
"""

import traceback

from influxdb import InfluxDBClient
from reactivex import operators as ops

from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive

client = InfluxDBClient(host="localhost", port=8086, database="ruuvi")


def try_write_to_influxdb(received_data):
    """
    Call the write_to_influxdb -method and catch any exceptions as any uncaught
    exception will kill the thread/process listening to events from a specific
    RuuviTag.
    """
    try:
        write_to_influxdb(received_data)
    except Exception:
        traceback.print_exc()


def write_to_influxdb(received_data):
    """
    Convert data into RuuviCollector naming scheme and scale and write to InfluxDB.
    """
    dataFormat = received_data[1].get("data_format", None)
    fields = {}
    fields["temperature"] = received_data[1].get("temperature", None)
    fields["humidity"] = received_data[1].get("humidity", None)
    fields["pressure"] = received_data[1].get("pressure", None)
    fields["accelerationX"] = received_data[1].get("acceleration_x", None)
    fields["accelerationY"] = received_data[1].get("acceleration_y", None)
    fields["accelerationZ"] = received_data[1].get("acceleration_z", None)
    fields["batteryVoltage"] = received_data[1]["battery"] / 1000.0 if ("battery" in received_data[1]) else None
    fields["txPower"] = received_data[1].get("tx_power", None)
    fields["movementCounter"] = received_data[1].get("movement_counter", None)
    fields["measurementSequenceNumber"] = received_data[1].get("measurement_sequence_number", None)
    fields["tagID"] = received_data[1].get("tagID", None)
    fields["rssi"] = received_data[1].get("rssi", None)
    json_body = [
        {
            "measurement": "ruuvi_measurements",
            "tags": {"mac": received_data[0], "dataFormat": dataFormat},
            "fields": fields,
        }
    ]
    client.write_points(json_body)


interval_in_s = 5.0

ruuvi_rx = RuuviTagReactive()

# Makes separate write to InfluxDB for each sensor as each subject generated by
# group_by is handled separately
ruuvi_rx.get_subject().pipe(ops.group_by(lambda x: x[0])).subscribe(
    lambda x: x.pipe(ops.sample(interval_in_s)).subscribe(try_write_to_influxdb)
)
