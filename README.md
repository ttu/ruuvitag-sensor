# RuuviTag Sensor Python Package

[ ![Codeship Status for ttu/ruuvitag-sensor](https://codeship.com/projects/5d8139b0-52ae-0134-2889-02adab5d782c/status?branch=master)](https://codeship.com/projects/171611)

RuuviTag Sensor is a Python library for communicating with [RuuviTag BLE Sensor Beacon](http://ruuvitag.com/) and for decoding sensord data from broadcasted eddystone-url.

### Installation

```sh
$ pip install git+https://github.com/ttu/ruuvitag-sensor

# or clone the repository and install locally
$ pip install -e .
```

### Usage

```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

sensor = RuuviTagSensor('AA-2C-6A-1E-59-3D', 'tets_name')

# update state from device
state = sensor.update()

# get latest state
state = sensor.state
```

If site-packages is in python path then ruuvitag_sensor can be used from commmand line:

```
$ python ruuvitag_sensor -l


usage: ruuvitag_sensor [-h] [-g MAC_ADDRESS] [-l] [--version]

optional arguments:
  -h, --help            show this help message and exit
  -g MAC_ADDRESS, --get MAC_ADDRESS
                        Get data
  -l, --list            List all devices
  --version             show program's version number and exit
```

### Tests

```sh
$ pip install nose
$ nosetests
# Or use setup.py
$ python setup.py test
```

### CI

Tests are ran automatically with Codeship. Codeship's Linux Virtual machine can't install gattlib, so therefore can't use setup.py and have to use requirements_test.txt with CI tests.

### Requirements

* Python < 3.5
    * gattlib won't install when using Python 3.5
* Linux
    * There is no working Windows BLE library for Python
    * Package's Windows support is only for testing and url decoding

## License

Licensed under the [MIT](LICENSE) License.