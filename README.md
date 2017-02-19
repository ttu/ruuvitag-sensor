# RuuviTag Sensor Python Package

[ ![Codeship Status for ttu/ruuvitag-sensor](https://codeship.com/projects/5d8139b0-52ae-0134-2889-02adab5d782c/status?branch=master)](https://codeship.com/projects/171611)

RuuviTag Sensor is a Python library for communicating with [RuuviTag BLE Sensor Beacon](http://ruuvitag.com/) and for decoding sensord data from broadcasted eddystone-url.

### Requirements

* RuuviTag with Weather Station firmware
    * Setup [guide](https://ruu.vi/setup/)
* Python 2.7 and 3
    * psutil
        * Package uses psutil to start and stop processes. Psutil requires `sudo apt-get install python-dev` or `sudo apt-get install python3-dev`
* Linux
    * Package's Windows and OSX supports are only for testing and url decoding
* Bluez
    * `sudo apt-get install bluez bluez-hcidump`
* Superuser rights
    * Package uses internally hciconf, hcitool and hcidump, which require superuser rights

### Installation

Install latest released version
```sh
$ pip install ruuvitag_sensor
```

Install latest developement version
```sh
$ pip install git+https://github.com/ttu/ruuvitag-sensor
# Or clone this repository and install locally
$ pip install -e .
```

Full installation guide for [Raspberry PI & Raspbian](https://github.com/ttu/ruuvitag-sensor/blob/master/install_guide_pi.md)

### Usage

RuuviTag sensors can be identified using MAC addresses.


##### Get data from sensor

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

sensor = RuuviTagSensor('AA:2C:6A:1E:59:3D')

# update state from the device
state = sensor.update()

# get latest state (does not get it from the device)
state = sensor.state

print(state)
```

##### Get sensor datas with callback

`get_datas` calls the callback every time when a RuuviTag sensor broadcasts data

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

def handle_data(found_data):
    print('MAC ' + found_data[0])
    print(found_data[1])

RuuviTagSensor.get_datas(handle_data)
```

Optional list of macs and run flag can be passed to the get_datas function. Callback is called only for macs in the list and setting run flag to false will stop execution. If run flag is not passed, function will execute forever.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag

counter = 10
# RunFlag for stopping execution at desired time
run_flag = RunFlag()

def handle_data(found_data):
    print('MAC ' + found_data[0])
    print(found_data[1])
    global counter
    counter = counter - 1
    if counter < 0:
        run_flag.running = False

# List of macs of sensors which will execute callback function
macs = ['AA:2C:6A:1E:59:3D', 'CC:2C:6A:1E:59:3D']

RuuviTagSensor.get_datas(handle_data, macs, run_flag)
```

##### Get data for specified sensors

`get_data_for_sensors` will collect latest data from sensors for specified duration.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

# List of macs of sensors which data will be collected
# If list is empty, data will be collected for all found sensors
macs = ['AA:2C:6A:1E:59:3D', 'CC:2C:6A:1E:59:3D']
# get_data_for_sensors will look data for the duration of timeout_in_sec
timeout_in_sec = 4

datas = RuuviTagSensor.get_data_for_sensors(macs, timeout_in_sec)

# Dictionary will have lates data for each sensor
print(datas['AA:2C:6A:1E:59:3D'])
print(datas['CC:2C:6A:1E:59:3D'])
```

##### Find sensors

`find_ruuvitags` function will exeute forever and when new RuuviTag sensor is found it will print it's MAC address and state at that moment. This function can be used with a command line applications.

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

RuuviTagSensor.find_ruuvitags()
```

##### Parse data

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.url_decoder import UrlDecoder

full_data = '043E2A0201030157168974A5F41E0201060303AAFE1616AAFE10EE037275752E76692341412C3E672B49246AB9'
data = full_data[26:]

encoded = RuuviTagSensor.convert_data(data)

sensor_data = UrlDecoder().decode_data(encoded)

print(sensor_data)
```

##### Command line

```
$ python ruuvitag_sensor -h

usage: ruuvitag_sensor [-h] [-g MAC_ADDRESS] [-f] [-l] [-s] [--version]

optional arguments:
  -h, --help            show this help message and exit
  -g MAC_ADDRESS, --get MAC_ADDRESS
                        Get data
  -f, --find            Find broadcasting RuuviTags
  -l, --latest          Get latest data for found RuuviTags
  -s, --stream          Stream broadcasts from all RuuviTags
  --version             show program's version number and exit
```

## Tests

Tests use unittest.mock library, so Python 3.3. or newer is required.

Run with nosetests

```sh
$ pip install nose
$ nosetests
```

Run with setup

```sh
$ python setup.py test
```

## Examples

Examples are in [examples](https://github.com/ttu/ruuvitag-sensor/tree/master/examples) directory.

## Change log

[Change Log](https://github.com/ttu/ruuvitag-sensor/blob/master/CHANGELOG.md)

## License

Licensed under the [MIT](https://github.com/ttu/ruuvitag-sensor/blob/master/LICENSE) License.