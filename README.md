# RuuviTag Sensor Python Package

RuuviTag Sensor is a Python library for communicating with [RuuviTag BLE Sensor Beacon](http://ruuvitag.com/) and for decoding sensord data from broadcasted eddystone-url.

* DONE: Url decode
* TODO: BLE communication

### Installation

### Usage

```sh
$ python ruuvitag_sensor [mac_address]
```

### Tests

```sh
$ pip install nose
$ nosetests
```

### Requirements

* Python 3.x

### Eddystone

[Eddystone Protocol Specification](https://github.com/google/eddystone/blob/master/protocol-specification.md)

* Bluetooth Service UUID used by Eddystone
    * 16bit: 0xfeaa 
    * 64bit: 0000FEAA-0000-1000-8000-00805F9B34FB
