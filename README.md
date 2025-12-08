RuuviTag Sensor Python Package
---------------------------------

[![Build Status](https://github.com/ttu/ruuvitag-sensor/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/ttu/ruuvitag-sensor/actions/workflows/build.yml)
[![License](https://img.shields.io/pypi/l/ruuvitag-sensor.svg)](https://pypi.python.org/pypi/ruuvitag-sensor/)
[![PyPI version](https://img.shields.io/pypi/v/ruuvitag-sensor.svg)](https://pypi.python.org/pypi/ruuvitag-sensor)
[![PyPI downloads](https://img.shields.io/pypi/dm/ruuvitag-sensor.svg)](https://pypistats.org/packages/ruuvitag-sensor)
[![Python versions](https://img.shields.io/badge/python-3.10+-blue.svg)](https://pypi.python.org/pypi/ruuvitag-sensor/)

`ruuvitag-sensor` is a Python package for communicating with [RuuviTag BLE Sensor](https://ruuvi.com/) and for decoding measurement data from broadcasted BLE data.

**Documentation website:** [https://ttu.github.io/ruuvitag-sensor/](https://ttu.github.io/ruuvitag-sensor/)

## Requirements

* RuuviTag sensor or Ruuvi Air
    * Setup [guide](https://ruuvi.com/quick-start/)
    * Supports [Data Format 2, 3, 4, 5, 6 and E1](https://docs.ruuvi.com/)
      * __Data Format 5:__ Used by RuuviTag sensors. See [RuuviTag Data Formats](#ruuvi-tag-data-formats) for more information.
      * __Data Format 6 and E1:__ Used by Ruuvi Air. See [Ruuvi Air Data Formats](#ruuvi-air-data-formats) for more information.
      * __NOTE:__ Data Formats 2, 3 and 4 are _deprecated_ and should not be used.
* [Bleak](https://github.com/hbldh/bleak) communication module (Windows, macOS and Linux)
    * Default adapter for all supported operating systems.
    * Bleak supports
      * [Async-methods](#usage)
      * [Observable streams](#usage)
      * [Fetch history data](#usage)
    * [Install guide](#Bleak)
* Bluez (Linux-only)
    * Bluez supports
      * [Sync-methods](#usage)
      * [Observable streams](#usage)
    * [Install guide](#BlueZ)
    * __NOTE:__ The BlueZ-adapter implementation uses deprecated BlueZ tools that are no longer supported.
      * Bleson-adapter supports sync-methods, but please be aware that it is not fully supported due to the alpha release status of the Bleson communication module. See [Bleson](#Bleson) for more information.
* Python 3.10+
    * For Python 3.9 support, check installation [instructions](#python-39) for an older version.
    * For Python 3.7 and 3.8 support, check installation [instructions](#python-37-and-38) for an older version.
    * For Python 2.x or <3.7 support, check installation [instructions](#python-2x-and-36-and-below) for an older version.


__NOTE: Major version changes__ 
* Version 4.0 supports only Python 3.10 and newer, adds support for Ruuvi Air sensors and allows Data Format to be specified as int or string.
* Version 3.0 changed default BLE adapter for all platforms to Bleak with async-methods. To use `Bluez`and sync-methods, check the installation [instructions](#BlueZ).
* Version 2.0 contains method renames. When using a version prior to 2.0, check the documentation and examples from [documentation](https://ttu.github.io/ruuvitag-sensor/#/1.2.1/) or in GitHub, switch to the correct release tag from _switch branches/tags_.


## Installation

Install the latest released version
```sh
$ python -m pip install ruuvitag-sensor
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

## Usage

### Fetch broadcast data from RuuviTags

The package provides 3 ways to fetch broadcasted data from sensors:

1. Asynchronously with async/await
2. Synchronously with callback
3. Observable streams with ReactiveX

RuuviTag sensors can be identified using MAC addresses. Methods return a tuple containing MAC and sensor data payload.

```py
('D2:A3:6E:C8:E0:25', {'data_format': 5, 'humidity': 47.62, 'temperature': 23.58, 'pressure': 1023.68, 'acceleration': 993.2331045630729, 'acceleration_x': -48, 'acceleration_y': -12, 'acceleration_z': 992, 'tx_power': 4, 'battery': 2197, 'movement_counter': 0, 'measurement_sequence_number': 88, 'mac': 'd2a36ec8e025', 'rssi': -80})
```

### Fetch stored history data from RuuviTags internal memory

4. Fetch history data with async/await

Each history entry contains one measurement type (temperature, humidity, or pressure) with a Unix timestamp (integer). RuuviTag sends each measurement type as a separate entry.

```py
[
    {'temperature': 22.22, 'humidity': None, 'pressure': None, 'timestamp': 1738476581}
    {'temperature': None, 'humidity': 38.8, 'pressure': None, 'timestamp': 1738476581},
    {'temperature': None, 'humidity': None, 'pressure': 35755.0, 'timestamp': 1738476581},
]
```


### 1. Get sensor data asynchronously with async/await

__NOTE:__ Asynchronous functionality works only with `Bleak`-adapter.

`get_data_async` returns the data whenever a RuuviTag sensor broadcasts data. `get_data_async` will execute until iterator is exited. This method is the preferred way to use the library with _Bleak_.

```py
import asyncio
from ruuvitag_sensor.ruuvi import RuuviTagSensor


async def main():
    async for found_data in RuuviTagSensor.get_data_async():
        print(f"MAC: {found_data[0]}")
        print(f"Data: {found_data[1]}")


if __name__ == "__main__":
    asyncio.run(main())
```

The optional list of MACs can be passed to the `get_data_async` function.

```py
import asyncio
from ruuvitag_sensor.ruuvi import RuuviTagSensor

macs = ["AA:2C:6A:1E:59:3D", "CC:2C:6A:1E:59:3D"]


async def main():
    # Get data only for defineded MACs. Exit after 10 found results
    datas = []
    async for found_data in RuuviTagSensor.get_data_async(macs):
        print(f"MAC: {found_data[0]}")
        print(f"Data: {found_data[1]}")
        datas.append(found_data)
        if len(datas) > 10:
            break


if __name__ == "__main__":
    asyncio.run(main())
```

The line `if __name__ == "__main__":` is required on Windows and macOS due to the way the `multiprocessing` library works. While not required on Linux, it is recommended. It is omitted from the rest of the examples below.

### 2. Get sensor data synchronously with callback

__NOTE:__ Synchronous functionality works only with `BlueZ`-adapter.

`get_data` calls the callback whenever a RuuviTag sensor broadcasts data. This method is the preferred way to use the library with _BlueZ_.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor


def handle_data(found_data):
    print(f"MAC {found_data[0]}")
    print(f"Data {found_data[1]}")


if __name__ == "__main__":
    RuuviTagSensor.get_data(handle_data)
```

The optional list of MACs and run flag can be passed to the `get_data` function. The callback is called only for MACs in the list and setting the run flag to false will stop execution. If the run flag is not passed, the function will execute forever.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag

counter = 10
# RunFlag for stopping execution at desired time
run_flag = RunFlag()


def handle_data(found_data):
    print(f"MAC: {found_data[0]}")
    print(f"Data: {found_data[1]}")

    global counter
    counter = counter - 1
    if counter < 0:
        run_flag.running = False


# List of MACs of sensors which will execute callback function
macs = ["AA:2C:6A:1E:59:3D", "CC:2C:6A:1E:59:3D"]

RuuviTagSensor.get_data(handle_data, macs, run_flag)
```

### 3. Get sensor data with observable streams (ReactiveX / RxPY)

`RuuviTagReactive` is a reactive wrapper and background process for RuuviTagSensor `get_data`. An optional MAC address list can be passed on the initializer and execution can be stopped with the stop function.

```python
from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive
from reactivex import operators as ops

ruuvi_rx = RuuviTagReactive()

# Print all notifications
ruuvi_rx.get_subject().\
    subscribe(print)

# Print only last data every 10 seconds for F4:A5:74:89:16:57
ruuvi_rx.get_subject().pipe(
      ops.filter(lambda x: x[0] == "F4:A5:74:89:16:57"),
      ops.buffer_with_time(10.0)
    ).subscribe(lambda data: print(data[len(data) - 1]))

# Execute only every time when temperature changes for F4:A5:74:89:16:57
ruuvi_rx.get_subject().pipe(
      ops.filter(lambda x: x[0] == "F4:A5:74:89:16:57"),
      ops.map(lambda x: x[1]["temperature"]),
      ops.distinct_until_changed()
    ).subscribe(lambda x: print(f"Temperature changed: {x}"))

# Close all connections and stop Bluetooth communication
ruuvi_rx.stop()
```

More [samples](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/reactive_extensions.py) and a simple [HTTP server](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/http_server_asyncio_rx.py) under the examples directory.

Check the official documentation of [ReactiveX](https://rxpy.readthedocs.io/en/latest/index.html) and the [list of operators](https://rxpy.readthedocs.io/en/latest/operators.html).

### 4. Fetch history data

__NOTE:__ History data functionality works only with `Bleak`-adapter.

RuuviTags with firmware version 3.30.0 or newer support retrieving historical measurements. The package provides two methods to access this data:

1. `get_history_async`: Stream history entries as they arrive
2. `download_history`: Download all history entries at once

Each history entry contains one measurement type (temperature, humidity, or pressure) with a Unix timestamp (integer). RuuviTag sends each measurement type as a separate entry.

Example history entry:
```py
{
    'temperature': 22.22,  # Only one measurement type per entry
    'humidity': None,
    'pressure': None,
    'timestamp': 1738476581  # Unix timestamp (integer)
}
```

```py
import asyncio
from datetime import datetime, timedelta, timezone

from ruuvitag_sensor.ruuvi import RuuviTagSensor


async def main():
    # Get history from the last 10 minutes
    start_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    
    # Stream entries as they arrive
    async for entry in RuuviTagSensor.get_history_async(mac="AA:BB:CC:DD:EE:FF", start_time=start_time):
        print(f"Time: {entry['timestamp']} - {entry}")
        
    # Or download all entries at once
    history = await RuuviTagSensor.download_history(mac="AA:BB:CC:DD:EE:FF", start_time=start_time)
    for entry in history:
        print(f"Time: {entry['timestamp']} - {entry}")


if __name__ == "__main__":
    asyncio.run(main())
```

__NOTE:__ Due to the way macOS handles Bluetooth, methods uses UUIDs to identify RuuviTags instead of MAC addresses.

### Other helper methods

#### Get data for specified sensors for a specific duration

`get_data_for_sensors` and `get_data_for_sensors_async` will collect the latest data from sensors for a specified duration.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

# List of MACs of sensors which data will be collected
# If list is empty, data will be collected for all found sensors
macs = ["AA:2C:6A:1E:59:3D", "CC:2C:6A:1E:59:3D"]
# get_data_for_sensors will look data for the duration of timeout_in_sec
timeout_in_sec = 4

data = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)
# data = await RuuviTagSensor.get_data_for_sensors_async(macs, timeout_in_sec)

# Dictionary will have latest data for each sensor
print(data["AA:2C:6A:1E:59:3D"])
print(data["CC:2C:6A:1E:59:3D"])
```

__NOTE:__ These methods shouldn't be used for a long duration with a short timeout. Methods will start and stop a new BLE scanning process with every method call. For long-running processes, it is recommended to use the `get_data`- and `get_data_async`-method.

#### Get data from a sensor

__NOTE:__ For a single sensor it is recommended to use `RuuviTagSensor.get_data` or `RuuviTagSensor.get_data_async` methods instead of `RuuviTag`- or `RuuviTagAsync`-class. `RuuviTagAsync`-class doesn't work with macOS, due to the way how macOS returns MAC address.

```python
from ruuvitag_sensor.ruuvitag import RuuviTag

sensor = RuuviTag("AA:2C:6A:1E:59:3D")

# update state from the device
state = sensor.update()

# get latest state (does not get it from the device)
state = sensor.state

print(state)
```

#### Find sensors

`RuuviTagSensor.find_ruuvitags` and `RuuviTagSensor.find_ruuvitags_async` methods will execute forever and when a new RuuviTag sensor is found, it will print its MAC address and state at that moment. This function can be used with command-line applications. Logging must be enabled and set to print to the console.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor
import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()

RuuviTagSensor.find_ruuvitags()
```

### Using different Bluetooth device

If you have multiple Bluetooth devices installed, the device to be used might not be the default (Linux: `hci0`). The device can be passed with a `bt_device` parameter.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvitag import RuuviTag

sensor = RuuviTag("F4:A5:74:89:16:57", "hci1")

RuuviTagSensor.find_ruuvitags("hci1")

data = RuuviTagSensor.get_data_for_sensors(bt_device="hci1")

RuuviTagSensor.get_data(lambda x: print(f"{x[0]} - {x[1]}"), bt_device=device))
```

### Parse data

```python
from ruuvitag_sensor.data_formats import DataFormats
from ruuvitag_sensor.decoder import get_decoder

full_data = "043E2A0201030157168974A51F0201060303AAFE1716AAFE10F9037275752E76692F23416A5558314D417730C3"
data = full_data[26:]

# convert_data returns tuple which has Data Format type and encoded data
(data_format, encoded) = DataFormats.convert_data(data)

sensor_data = get_decoder(data_format).decode_data(encoded)

print(sensor_data)
# {'temperature': 25.12, 'identifier': '0', 'humidity': 26.5, 'pressure': 992.0}
```

## Data Formats

### RuuviTag Data Formats

RuuviTag sensors support multiple data formats. Example data from sensors with different firmware:
* Data Format 2 (URL) - Deprecated
* Data Format 3 (RAW) - Deprecated  
* Data Format 4 (URL with identifier) - Deprecated
* Data Format 5 (RAW v2)

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

The original reason to use URL-encoded data was to use _Google's Nearby_ notifications to let users view tags without the need to install any app. Since _Google's Nearby_ has been discontinued, there isn't any benefit in using the Eddystone format anymore.

### Ruuvi Air Data Formats

#### Data Format 6

Ruuvi Air uses Data Format 6 for comprehensive indoor air quality monitoring. For more details, see the [official specification](https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-6).

Example data from a Ruuvi Air sensor:

```python
{
'4C:88:4F:AA:BB:CC': { 'data_format': 6, 'temperature': 29.5, 'humidity': 55.3, 'pressure': 1011.02, 'pm_2_5': 11.2, 'co2': 201, 'voc': 10, 'nox': 2, 'luminosity': 13026.67, 'measurement_sequence_number': 205, 'calibration_in_progress': False, 'mac': '4c884f' }
}
```

#### Data Format E1

Ruuvi Air uses Data Format E1 to extend format 6 data. If same Ruuvi Air device provides both, format 6 and E1 data, the format 6 data should be discarded as E1 data includes all format 6 data fields. For more details, see the [official specification](https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-e1).

Example data from a Ruuvi Air sensor:

```python
{
'CB:B8:33:4C:88:4F', {'data_format': 'E1', 'humidity': 55.3, 'temperature': 29.5, 'pressure': 1011.02, 'pm_1': 10.1, 'pm_2_5': 11.2, 'pm_4': 121.3, 'pm_10': 455.4, 'co2': 201, 'voc': 20, 'nox': 4, 'luminosity': 13027.0, 'measurement_sequence_number': 14601710, 'calibration_in_progress': True, 'mac': 'CB:B8:33:4C:88:4F'}
}
```

## Logging

The package uses Python's standard `logging` module. Each module in the package creates its own logger using `logging.getLogger(__name__)`.

### Library usage

When using ruuvitag-sensor as a library in your application, you should configure logging according to your application's needs:

```py
import logging
from ruuvitag_sensor.ruuvi import RuuviTagSensor

# Configure logging at the application level
logging.basicConfig(level=logging.INFO)
# Or set up custom handlers, formatters, etc.

data = RuuviTagSensor.get_data_for_sensors()
```

### Command-line and script usage

For command-line and script usage, the package provides convenience functions to enable console output:

```py
from ruuvitag_sensor.ruuvi import RuuviTagSensor
import ruuvitag_sensor.log

# Enable console logging (defaults to INFO level)
ruuvitag_sensor.log.enable_console()

# For debug logging
ruuvitag_sensor.log.enable_console(level=logging.DEBUG)

data = RuuviTagSensor.get_data_for_sensors()
```

### Log all events to log-file

By default only errors are logged to `ruuvitag_sensor.log`-file. The level can be changed by changing FileHandler's log level.

```py
import logging
from ruuvitag_sensor.log import log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

log.setLevel(logging.DEBUG)

for handler in log.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.setLevel(logging.DEBUG)

data = RuuviTagSensor.get_data_for_sensors()
```

### A custom event handler for a specific log event

You can add custom handlers to respond to specific log events. For example, to exit when a specific sensor is blacklisted:

```py
from logging import StreamHandler
from ruuvitag_sensor.log import log
from ruuvitag_sensor.ruuvi import RuuviTagSensor


class ExitHandler(StreamHandler):

    def emit(self, record):
        if record.levelname != "DEBUG":
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

## BLE Communication modules

### BlueZ

BlueZ works only on __Linux__. When using BlueZ, Windows and macOS support is only for testing with hard-coded data and for data decoding.

BlueZ tools require __superuser__ rights.

Install BlueZ.

```sh
$ sudo apt-get install bluez bluez-hcidump
```

`ruuvitag-sensor` package uses internally _hciconfig_, _hcitool_ and _hcidump_. These tools are deprecated. In case tools are missing, an older version of BlueZ is required ([Issue](https://github.com/ttu/ruuvitag-sensor/issues/31))

Enable Bluez with the `RUUVI_BLE_ADAPTER` environment variable.

```sh
$ export RUUVI_BLE_ADAPTER="bluez"
```

Or use `os.environ`. __NOTE:__ this must be set before importing `ruuvitag_sensor`.

```py
import os

os.environ["RUUVI_BLE_ADAPTER"] = "bluez"
```

And install ptyprocess.

```sh
python -m pip install ptyprocess
```

#### BlueZ limitations

`ruuvitag-sensor` package uses BlueZ to listen to broadcasted BL information (uses _hciconf_, _hcitool_, _hcidump_). Implementation does not handle well all unexpected errors or changes, e.g. when the adapter is busy, rebooted or powered down.

In case of errors, the application tries to exit immediately, so it can be automatically restarted.

### Bleak

Bleak is automatically installed with `ruuvitag-sensor` package on all platforms.
It is automatically used with `ruuvitag-sensor` package on all platforms.

Bleak only supports asynchronous methods.

```py
import asyncio
from ruuvitag_sensor.ruuvi import RuuviTagSensor


async def main():
    async for data in RuuviTagSensor.get_data_async():
        print(data)


if __name__ == "__main__":
    asyncio.run(main())
```

Check [get_async_bleak](https://github.com/ttu/ruuvitag-sensor/blob/master/examples/get_async_bleak.py) and other async examples from [examples](https://github.com/ttu/ruuvitag-sensor/tree/master/examples) directory.

#### Bleak dummy BLE data

Bleak-adapter has a development-time generator for dummy data, which can be useful during development if no sensors are available. Set the `RUUVI_BLE_ADAPTER` environment variable to `bleak_dev`.

### Bleson

Current state and known bugs in [issue #78](https://github.com/ttu/ruuvitag-sensor/issues/78).

[Bleson](https://github.com/TheCellule/python-bleson) works with Linux, macOS and partially with Windows.

Bleson is not installed automatically with `ruuvitag-sensor` package. Install it manually from GitHub.

```sh
$ python -m pip install git+https://github.com/TheCellule/python-bleson
```

Add environment variable `RUUVI_BLE_ADAPTER` with value `bleson`. E.g.

```sh
$ export RUUVI_BLE_ADAPTER="bleson"
```

__NOTE:__ On macOS, only Data Format 5 works, as macOS doesn't advertise MAC address and only DF5 has MAC in sensor payload. `RuuviTag`-class doesn't work with macOS.

__NOTE:__ On Windows, Bleson requires _Python 3.6_. Unfortunately on Windows, Bleson doesn't send any payload for the advertised package, so it is still unusable.


## Python 3.9

Last version of `ruuvitag-sensor` with Python 3.9 support is [3.1.0](https://pypi.org/project/ruuvitag-sensor/3.1.0/).

[Branch](https://github.com/ttu/ruuvitag-sensor/tree/release/3.1.0) / [Tag / commit](https://github.com/ttu/ruuvitag-sensor/commit/e722700e21b75adfcec515c640d447f6e701bf1b)

```sh
$ git checkout release/3.1.0
```

Install from PyPI
```sh
$ python -m pip install ruuvitag-sensor==3.1.0
```


## Python 3.7 and 3.8

Last version of `ruuvitag-sensor` with Python 3.7 and 3.8 support is [2.3.1](https://pypi.org/project/ruuvitag-sensor/2.3.1/).

[Branch](https://github.com/ttu/ruuvitag-sensor/tree/release/2.3.1) / [Tag / commit](https://github.com/ttu/ruuvitag-sensor/commit/b16c9580d75eafe5508d0551642eb3b022ae1325)

```sh
$ git checkout release/2.3.1
```

Install from PyPI
```sh
$ python -m pip install ruuvitag-sensor==2.3.1
```

## Python 2.x and 3.6 and below

Last version of `ruuvitag-sensor` with Python 2.x and <3.7 support is [1.2.1](https://pypi.org/project/ruuvitag-sensor/1.2.1/).

[Branch](https://github.com/ttu/ruuvitag-sensor/tree/release/1.2.1) / [Tag / commit](https://github.com/ttu/ruuvitag-sensor/commit/12ca3cfcb7fbed28477bb34f3bffd3eee0f9888d)

```sh
$ git checkout release/1.2.1
```

Install from PyPI
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

[Notes for developers](https://github.com/ttu/ruuvitag-sensor/blob/master/developer_notes.md) who are interested in developing `ruuvitag-sensor` package or are interested in its internal functionality.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

Licensed under the [MIT](https://github.com/ttu/ruuvitag-sensor/blob/master/LICENSE) License.
