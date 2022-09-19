# RuuviTag Sensor Python Package

[![Build Status](https://app.travis-ci.com/ttu/ruuvitag-sensor.svg?branch=master)](https://app.travis-ci.com/github/ttu/ruuvitag-sensor) [![PyPI](https://img.shields.io/pypi/v/ruuvitag_sensor.svg)](https://pypi.python.org/pypi/ruuvitag_sensor)

RuuviTag Sensor is a Python library for communicating with [RuuviTag BLE Sensor Beacon](https://ruuvi.com/) and for decoding measurement data from broadcasted BLE data.

### Requirements

* RuuviTag with Weather Station firmware
    * Setup [guide](https://lab.ruuvi.com/start/)
    * Supports [Data Format 2, 3, 4 and 5](https://github.com/ruuvi/ruuvi-sensor-protocols)
      * __NOTE:__ Data Formats 2, 3 and 4 are _deprecated_ and should not be used
* Bluez (Linux-only)
    * [BlueZ install guide](#BlueZ)
* __BETA:__ Cross-platform BLE adapters
    * [Bleak](https://github.com/hbldh/bleak) communication module
      * Bleak only supports async methods (work in progress)
      * [Bleak install guide](#Bleak)
    * [Bleson](https://github.com/TheCellule/python-bleson) communication module
      * [Bleson install guide](#Bleson)
* Python 3.7+
    * For Python 2.x or <3.7 support, check [installation instructions](#python-2x-and-36-and-below) for an older version

__NOTE:__ Version 2.0 contains method renames. When using a version prior to 2.0, check the documentation and examples from [pypi](https://pypi.org/project/ruuvitag-sensor/) or in GitHub switch to the correct release tag from _switch branches/tags_.

### Installation

Install the latest released version
```sh
$ python -m pip install ruuvitag_sensor
```

Install the latest development version
```sh
$ python -m venv .venv
$ source .venv/bin/activate
$ python -m pip install git+https://github.com/ttu/ruuvitag-sensor

# For development, clone this repository and install for development in editable mode
$ python -m pip install -e .[dev]
```

Full installation guide for [Raspberry PI & Raspbian](https://github.com/ttu/ruuvitag-sensor/blob/master/install_guide_pi.md)

### Usage

The package provides 3 ways to fetch data from sensors:

1. Synchronously with callback
2. Asynchronously with async/await (BETA)
3. Observable streams with ReactiveX

RuuviTag sensors can be identified using MAC addresses. Methods return a tuple with MAC and sensor data payload.

```py
('D2:A3:6E:C8:E0:25', {'data_format': 5, 'humidity': 47.62, 'temperature': 23.58, 'pressure': 1023.68, 'acceleration': 993.2331045630729, 'acceleration_x': -48, 'acceleration_y': -12, 'acceleration_z': 992, 'tx_power': 4, 'battery': 2197, 'movement_counter': 0, 'measurement_sequence_number': 88, 'mac': 'd2a36ec8e025', 'rssi': -80})
```

#### 1. Get sensor data synchronously with callback

`get_data` calls the callback whenever a RuuviTag sensor broadcasts data. This method is the preferred way to use the library.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor


def handle_data(found_data):
    print(f'MAC {found_data[0]}')
    print(f'Data {found_data[1]}')

if __name__ == '__main__':
    RuuviTagSensor.get_data(handle_data)
```

The line `if __name__ == '__main__':` is required on Windows and macOS due to the way the `multiprocessing` library works. It is not required on Linux, but it is recommended. It is omitted from the rest of the examples below.

The optional list of MACs and run flag can be passed to the `get_data` function. The callback is called only for MACs in the list and setting the run flag to false will stop execution. If the run flag is not passed, the function will execute forever.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag

counter = 10
# RunFlag for stopping execution at desired time
run_flag = RunFlag()

def handle_data(found_data):
    print(f'MAC: {found_data[0]}')
    print(f'Data: {found_data[1]}')

    global counter
    counter = counter - 1
    if counter < 0:
        run_flag.running = False

# List of MACs of sensors which will execute callback function
macs = ['AA:2C:6A:1E:59:3D', 'CC:2C:6A:1E:59:3D']

RuuviTagSensor.get_data(handle_data, macs, run_flag)
```

#### 2. Get sensor data asynchronously

__NOTE:__ Asynchronous functionality is currently in beta-state and works only with `Bleak`-adapter.

```py
import asyncio
from ruuvitag_sensor.ruuvi import RuuviTagSensor


async def main():
    async for found_data in RuuviTagSensor.get_data_async():
        print(f'MAC: {found_data[0]}')
        print(f'Data: {found_data[1]}')

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
```

The optional list of MACs and run flag can be passed to the `get_data_async` function.

#### 3. Get sensor data with observable streams (ReactiveX / RxPY)

`RuuviTagReactive` is a reactive wrapper and background process for RuuviTagSensor `get_data`. Optional MAC address list can be passed on initializer and execution can be stopped with the stop function.

```python
from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive
from reactivex import operators as ops

ruuvi_rx = RuuviTagReactive()

# Print all notifications
ruuvi_rx.get_subject().\
    subscribe(print)

# Print only last data every 10 seconds for F4:A5:74:89:16:57
ruuvi_rx.get_subject().pipe(
      ops.filter(lambda x: x[0] == 'F4:A5:74:89:16:57'),
      ops.buffer_with_time(10.0)
    ).subscribe(lambda data: print(data[len(data) - 1]))

# Execute only every time when temperature changes for F4:A5:74:89:16:57
ruuvi_rx.get_subject().pipe(
      ops.filter(lambda x: x[0] == 'F4:A5:74:89:16:57'),
      ops.map(lambda x: x[1]['temperature']),
      ops.distinct_until_changed()
    ).subscribe(lambda x: print('Temperature changed: {}'.format(x)))

# Close all connections and stop bluetooth communication
ruuvi_rx.stop()
```

More [samples](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/reactive_extensions.py) and a simple [HTTP server](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/http_server_asyncio_rx.py) under the examples directory.

Check official documentation of [ReactiveX](https://rxpy.readthedocs.io/en/latest/index.html) and the [list of operators](https://rxpy.readthedocs.io/en/latest/operators.html).

#### Other helper methods

##### Get data for specified sensors for a specific duration

`get_data_for_sensors` will collect the latest data from sensors for a specified duration.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

# List of MACs of sensors which data will be collected
# If list is empty, data will be collected for all found sensors
macs = ['AA:2C:6A:1E:59:3D', 'CC:2C:6A:1E:59:3D']
# get_data_for_sensors will look data for the duration of timeout_in_sec
timeout_in_sec = 4

data = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)

# Dictionary will have latest data for each sensor
print(data['AA:2C:6A:1E:59:3D'])
print(data['CC:2C:6A:1E:59:3D'])
```

__NOTE:__ This method shouldn't be used for a long duration with a short timeout. `get_data_for_sensors` will start and stop a new BLE scanning process with every method call. For long-running processes, it is recommended to use `get_data`-method.

##### Get data from a sensor

__NOTE:__ For a single sensor it is recommended to use `RuuviTagSensor.get_data` or `RuuviTagSensor.get_data_for_sensors` methods instead of `RuuviTag`-class.

```python
from ruuvitag_sensor.ruuvitag import RuuviTag

sensor = RuuviTag('AA:2C:6A:1E:59:3D')

# update state from the device
state = sensor.update()

# get latest state (does not get it from the device)
state = sensor.state

print(state)
```

##### Find sensors

`RuuviTagSensor.find_ruuvitags` and `RuuviTagSensor.find_ruuvitags_async` methods will execute forever and when a new RuuviTag sensor is found, it will print its MAC address and state at that moment. This function can be used with command line applications. Logging must be enabled and set to print to console.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor
import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()

RuuviTagSensor.find_ruuvitags()
```

### Using different Bluetooth device

If you have multiple Bluetooth devices installed, a device to be used might not be the default (Linux: hci0). The device can be passed with `bt_device` parameter.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvitag import RuuviTag

sensor = RuuviTag('F4:A5:74:89:16:57', 'hci1')

RuuviTagSensor.find_ruuvitags('hci1')

data = RuuviTagSensor.get_data_for_sensors(bt_device='hci1')

RuuviTagSensor.get_data(lambda x: print('%s - %s' % (x[0], x[1]), bt_device=device))
```

#### Parse data

```python
from ruuvitag_sensor.data_formats import DataFormats
from ruuvitag_sensor.decoder import get_decoder

full_data = '043E2A0201030157168974A51F0201060303AAFE1716AAFE10F9037275752E76692F23416A5558314D417730C3'
data = full_data[26:]

# convert_data returns tuple which has Data Format type and encoded data
(data_format, encoded) = DataFormats.convert_data(data)

sensor_data = get_decoder(data_format).decode_data(encoded)

print(sensor_data)
# {'temperature': 25.12, 'identifier': '0', 'humidity': 26.5, 'pressure': 992.0}
```

### Data Formats

Example data has data from 4 sensors with different firmware.
* 1st is Data Format 2 (URL), the identifier is None as the sensor doesn't broadcast any identifier data
* 2nd is Data Format 4 (URL) and it has an identifier character
* 3rd is Data Format 3 (RAW)
* 4th is Data Format 5 (RAW v2)

```python
{
'CA:F7:44:DE:EB:E1': { 'data_format': 2, 'temperature': 22.0, 'humidity': 28.0, 'pressure': 991.0, 'identifier': None, 'rssi': None },
'F4:A5:74:89:16:57': { 'data_format': 4, 'temperature': 23.24, 'humidity': 29.0, 'pressure': 991.0, 'identifier': '0', 'rssi': None },
'A3:GE:2D:91:A4:1F': { 'data_format': 3, 'battery': 2899, 'pressure': 1027.66, 'humidity': 20.5, 'acceleration': 63818.215675463696, 'acceleration_x': 200.34, 'acceleration_y': 0.512, 'acceleration_z': -200.42, 'temperature': 26.3, 'rssi': None },
'CB:B8:33:4C:88:4F': { 'data_format': 5, 'battery': 2.995, 'pressure': 1000.43, 'mac': 'cbb8334c884f', 'measurement_sequence_number': 2467, 'acceleration_z': 1028, 'acceleration': 1028.0389097694697, 'temperature': 22.14, 'acceleration_y': -8, 'acceleration_x': 4, 'humidity': 53.97, 'tx_power': 4, 'movement_counter': 70, 'rssi': -65 }
}
```

#### Note on Data Format 2 and 4

There is no reason to use Data Format 2 or 4.

The original reasoning to use the URL-encoded data was to use _Google's Nearby_ notifications to let users view tags without the need to install any app. Since _Google's Nearby_ has been discontinued, there isn't any benefit in using the Eddystone format anymore.

### Logging and Printing to console

Logging can be enabled by importing `ruuvitag_sensor.log`. Console print can be enabled by calling `ruuvitag_sensor.log.enable_console()`. The command line application has console logging enabled by default.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor
import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()

data = RuuviTagSensor.get_data_for_sensors()

print(data)
```

#### Log all events to log-file

By default only errors are logged to `ruuvitag_sensor.log`-file. The level can be changed by changing FileHandler's log level.

```py
import logging
from ruuvitag_sensor.log import log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

for handler in log.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.setLevel(logging.DEBUG)

data = RuuviTagSensor.get_data_for_sensors()
```

### A custom event handler for a specific log event

If custom functionality is required when a specific event happens, e.g. exit when a specific sensor is blacklisted, logging event handlers can be utilized for this functionality.

```py
from logging import StreamHandler
from ruuvitag_sensor.log import log
from ruuvitag_sensor.ruuvi import RuuviTagSensor


class ExitHandler(StreamHandler):

    def emit(self, record):
        if (record.levelname != "DEBUG"):
            return
        msg = self.format(record)
        if "Blacklisting MAC F4:A5:74:89:16:57E" in msg:
            exit(1)


exit_handler = ExitHandler()
log.addHandler(exit_handler)

data = RuuviTagSensor.get_data_for_sensors()
```

## Command line application

```
$ python ruuvitag_sensor -h

usage: ruuvitag_sensor [-h] [-g MAC_ADDRESS] [-d BT_DEVICE] [-f] [-l] [-s] [--version]

optional arguments:
  -h, --help            show this help message and exit
  -g MAC_ADDRESS, --get MAC_ADDRESS
                        Get data
  -d BT_DEVICE, --device BT_DEVICE
                        Set Bluetooth device id (default hci0)
  -f, --find            Find broadcasting RuuviTags
  -l, --latest          Get latest data for found RuuviTags
  -s, --stream          Stream broadcasts from all RuuviTags
  --version             show program's version number and exit
```

## BlueZ

BlueZ works only on __Linux__. When using BlueZ, Windows and macOS support is only for testing with hard-coded data and for data decoding.

BlueZ tools require __superuser__ rights.

Install BlueZ.

```sh
$ sudo apt-get install bluez bluez-hcidump
```

Ruuvitag_sensor package uses internally _hciconfig_, _hcitool_ and _hcidump_. These tools are deprecated. In case tools are missing, an older version of BlueZ is required ([Issue](https://github.com/ttu/ruuvitag-sensor/issues/31))

### BlueZ limitations

`Ruuvitag_sensor` package uses BlueZ to listen broadcasted BL information (uses _hciconf_, _hcitool_, _hcidump_). Implementation does not handle well all unexpected errors or changes, e.g. when the adapter is busy, rebooted or powered down.

In case of errors, the application tries to exit immediately, so it can be automatically restarted.

## Bleak

Bleak is not installed automatically with `ruuvitag_sensor` package. Install it manually from pypi.

```sh
$ python -m pip install bleak
```

Add environment variable RUUVI_BLE_ADAPTER with value Bleak. E.g.

```sh
$ export RUUVI_BLE_ADAPTER="Bleak"
```

Bleak supports only async methods.

```py
import asyncio
from ruuvitag_sensor.ruuvi import RuuviTagSensor


async def main():
    async for data in RuuviTagSensor.get_data_async():
        print(data)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
```

Check [get_async_bleak](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/get_async_bleak.py) from examples.

### Bleak dummy BLE data

Bleak-adapter has a development-time generator for dummy data, which can be useful during development, when there are no sensors available. Set `RUUVI_BLE_ADAPTER` environment variable to `bleak_dev`.

## Bleson

Current state and known bugs in [issue #78](https://github.com/ttu/ruuvitag-sensor/issues/78).

Bleson works with Linux, macOS and partially with Windows.

Bleson is not installed automatically with `ruuvitag_sensor` package. Install it manually from GitHub.

```sh
$ pip install git+https://github.com/TheCellule/python-bleson
```

Add environment variable `RUUVI_BLE_ADAPTER` with value `Bleson`. E.g.

```sh
$ export RUUVI_BLE_ADAPTER="Bleson"
```

__NOTE:__ On macOS, only Data Format 5 works as macOS doesn't advertise MAC address and only DF5 has MAC in sensor payload. `RuuviTag`-class doesn't work with macOS.

__NOTE:__ On Windows, Bleson requires _Python 3.6_. Unfortunately on Windows, Bleson doesn't send any payload for the advertised package, so it is still unusable.


## Python 2.x and 3.6 and below

Last version of ruuvitag-sensor with Python 2.x and <3.7 support is [1.2.1](https://pypi.org/project/ruuvitag-sensor/1.2.1/).

[Branch](https://github.com/ttu/ruuvitag-sensor/tree/release/1.2.1) / [Tag / commit](https://github.com/ttu/ruuvitag-sensor/commit/12ca3cfcb7fbed28477bb34f3bffd3eee0f9888d)

```sh
$ git checkout release/1.2.1
```

Install from pypi
```sh
$ python -m pip install ruuvitag-sensor==1.2.1
```

## Examples

Examples are in [examples](https://github.com/ttu/ruuvitag-sensor/tree/master/examples) directory, e.g.

* Keep track of each sensor's current status and send updated data to the server. [Sync](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/send_updated_sync.py) and [async](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/send_updated_async.py) version.
* Send found sensor data to InfluxDB. [Reactive](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/post_to_influxdb_rx.py) and [non-reactive](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/post_to_influxdb.py) version. The naming convention of sent data matches [RuuviCollector library](https://github.com/scrin/ruuvicollector).
* Simple HTTP Server for serving found sensor data. [Flask](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/http_server.py), [aiohttp](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/http_server_asyncio.py) and [aiohttp with ReactiveX](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/http_server_asyncio_rx.py).

## Changelog

[Changelog](https://github.com/ttu/ruuvitag-sensor/blob/master/CHANGELOG.md)

## Developer notes

[Notes for developers](https://github.com/ttu/ruuvitag-sensor/blob/master/developer_notes.md) who are interested in developing RuuviTag Sensor package or are interested in its internal functionality.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

Licensed under the [MIT](https://github.com/ttu/ruuvitag-sensor/blob/master/LICENSE) License.
