# RuuviTag Sensor Python Package

[ ![Codeship Status for ttu/ruuvitag-sensor](https://codeship.com/projects/5d8139b0-52ae-0134-2889-02adab5d782c/status?branch=master)](https://codeship.com/projects/171611)

RuuviTag Sensor is a Python library for communicating with [RuuviTag BLE Sensor Beacon](http://ruuvitag.com/) and for decoding sensord data from broadcasted eddystone-url.

### Installation

```sh
$ pip install -e .
```

### Usage

```
usage: ruuvitag_sensor [-h] [-g MAC_ADDRESS] [-l] [--version]

optional arguments:
  -h, --help            show this help message and exit
  -g MAC_ADDRESS, --get MAC_ADDRESS
                        Get data
  -l, --list            List all devices
  --version             show program's version number and exit
```
e.g.
```sh
$ python ruuvitag_sensor -l
```

### Tests

```sh
$ pip install nose
$ nosetests
# Or use setup.py
$ python setup.py test
```

### CI

Tests are ran automatically with Codeship. Codeship's Linux Virtual machine can't install gattlib, so therefore can't use setup.py and have to use requirements_test.txt to be used with CI tests.

### Requirements

* Python 3.x
* Linux
    * BLE doesn't work yet on Windows

### Eddystone

[Eddystone Protocol Specification](https://github.com/google/eddystone/blob/master/protocol-specification.md)

* Bluetooth Service UUID used by Eddystone
    * 16bit: 0xfeaa 
    * 64bit: 0000FEAA-0000-1000-8000-00805F9B34FB
