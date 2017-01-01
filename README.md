# RuuviTag Sensor Python Package

[ ![Codeship Status for ttu/ruuvitag-sensor](https://codeship.com/projects/5d8139b0-52ae-0134-2889-02adab5d782c/status?branch=master)](https://codeship.com/projects/171611)

RuuviTag Sensor is a Python library for communicating with [RuuviTag BLE Sensor Beacon](http://ruuvitag.com/) and for decoding sensord data from broadcasted eddystone-url.

### Requirements

* RuuviTag with Weather Station firmware
    * Configuration [Guide](https://ruu.vi/configure/)
* Python 2.7 and 3.x
* Linux
    * Package's Windows and OSX supports are only for testing and url decoding
* Bluez
    * `sudo apt-get install bluez bluez-hcidump`

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

### Usage

#### Get data from sensor

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

sensor = RuuviTagSensor('AA:2C:6A:1E:59:3D')

# update state from the device
state = sensor.update()

# get latest state (does not get it from the device)
state = sensor.state
```

You can get address of the devce e.g. find sensors command or with hcitool

```sh
$ python ruuvitag_sensor -f
$ hcitool lescan
```

#### Find sensors

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

sensors = RuuviTagSensor.find_ruuvitags()

print(sensors)
```

#### Parse data

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.url_decoder import UrlDecoder

full_data = '043E2A0201030157168974A5F41E0201060303AAFE1616AAFE10EE037275752E76692341412C3E672B49246AB9'
data = full_data[26:]

decoded = RuuviTagSensor.decode_data(data)

url_decoder = UrlDecoder()
sensor_data = url_decoder.get_data(decoded)

print(sensor_data)
```

#### Command line

```
$ python ruuvitag_sensor -h

usage: ruuvitag_sensor [-h] [-g MAC_ADDRESS] [-f] [--version]

optional arguments:
  -h, --help            show this help message and exit
  -g MAC_ADDRESS, --get MAC_ADDRESS
                        Get data
  -f, --find            Find broadcasting RuuviTags
  --version             show program's version number and exit
```

## Tests

Run with nosetests

```sh
$ pip install nose
$ nosetests
```

Run with setup

```sh
$ python setup.py test
```

## License

Licensed under the [MIT](LICENSE) License.