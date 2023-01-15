#!/bin/python3
"""
Get data from sensors and post it to specified mqtt channel in json-format

Requires:
    Ruuvitag sensor - pip3 install --user ruuvitag-sensor
    Paho MQTT       - pip3 install --user paho-mqtt

Example usage:
./post_to_mqtt.py --mac DE:AD:BE:EE:EE:FF -b mqtt.ikenet \
     -t ruuvitag/sauna -i 60 -l saunassa

See here how to automate this using Ansible:
https://github.com/RedHatNordicsSA/iot-hack/blob/master/run-ruuvi-to-mqtt.yml
"""

import argparse
import json
import signal
import sys
import time

import paho.mqtt.client as mqtt
from paho.mqtt import publish

from ruuvitag_sensor.ruuvitag import RuuviTag

parser = argparse.ArgumentParser(
    description='Program relays Ruuvitag BLE temperature and humidity'
    'advertisements to MQTT broker.')
parser.add_argument(
    '-m', '--mac', dest='mac_address', required=True,
    help='Ruuvitag MAC address')
parser.add_argument(
    '-b', '--broker', dest='mqtt_broker', required=True,
    help='mqtt broker address, ip or fqdn')
parser.add_argument(
    '-t', '--topic', dest='mqtt_topic', required=True,
    help='mqtt topic, e.g. ruuvitag/sauna')
parser.add_argument(
    '-a', '--all', action='store_true', required=False,
    help='send all Ruuvitag values')
parser.add_argument(
    '-i', '--interval', dest='interval', default=60,
    type=int, required=False,
    help='seconds to wait between data queries')
parser.add_argument(
    '-l', '--location', dest='location', required=False,
    help='additional location tag for json')
args = parser.parse_args()

mac_address = args.mac_address
mqtt_broker = args.mqtt_broker
mqtt_topic = args.mqtt_topic
interval = args.interval
send_all = args.all
location = args.location


# let's trap ctrl-c, SIGINT and come down nicely
# pylint: disable=unused-argument,redefined-outer-name
def signal_handler(signal, frame):
    print('\nterminating gracefully.')
    client.disconnect()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# The callback for when the client receives a CONNACK response from the MQTT server.
# pylint: disable=unused-argument,redefined-outer-name
def on_connect(client, userdata, flags, rc):
    print(f'Connected to MQTT broker with result code {str(rc)}')

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe('$SYS/#')


client = mqtt.Client()
client.on_connect = on_connect
client.connect(mqtt_broker, 1883, 60)
client.loop_start()

print('Start listening to Ruuvitag')

sensor = RuuviTag(mac_address)
while True:

    # update state from the device
    state = sensor.update()

    if location:
        state['location'] = location
    else:
        state['location'] = mac_address

    if send_all:
        mqtt_msg = json.dumps(state)
    else:
        # extract temp and humidity values, and format data into custom JSON
        for_json = {
            'location': state['location'],
            'temperature': round(state['temperature'], 1),
            'humidity': round(state['humidity'], 1)
        }
        mqtt_msg = json.dumps(for_json)

    publish.single(mqtt_topic, mqtt_msg, hostname=mqtt_broker)
    print('.', end='', flush=True)

    time.sleep(interval)
