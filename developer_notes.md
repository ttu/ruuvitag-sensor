# RuuviTag Sensor Package Developer Notes

> Notes for developers who are interested in developing RuuviTag Sensor package or interested in it's internal functionality.

## Getting started

1. Clone the repository

2. Create virtualenv and activate it

```sh
$ python -m venv .venv
$ source .venv/bin/activate
```

3. Install required dependencies
```sh
$ sudo python -m pip install -e .
```

If virtualenv and/or pip are not installed, follow installation instructions show in the terminal.

4. Test that application works 
```sh
$ sudo python ruuvitag_sensor --help
```

## Project files

* adapters
  * nix_hci.py
    * Bluetooth LE communication (BlueZ)
  * bleson.py
    * Bluetooth LE communication (Bleson)
  * nix_hci_file.py
    * Emulate Bluetooth LE communication (file)
  * dummy.py
    * Emulate Bluetooth LE communication (hard coded values)
* data_formats.py
  * Data format decision logic and raw data encoding 
* decoder.py
  * Decode encoded data to readable dictionary
* log.py
  * Module level logging
* ruuvi_rx.py
  * RuuviTagReactive-class
    * Reactive wrapper and background process for RuuviTagSensor get_datas
* ruuvi.py
  * RuuviTagSensor-class
    * Main communicaton logic
    * This is the class mainly used
* ruuvitag.py
  * RuuviTag Sensors object
     * Helper class to be used to handle singe RuuviTag and it's state.


## Testing
To check that your changes work across multiple python versions and platforms, we have tox. 
You can run tox locally, but tox will only run your current platform and the python versions 
you have in your system. Travis, however, will pick up all the combinations and test the all.

## Update RuuviTag firmware and change modes

1. Download firmware from https://lab.ruuvi.com/dfu
1. Hold down `B` and press `R` (red light will turn on)
1. Open nRF Connect (Android) and connect to correct ruuvitag
1. Select DFU icon and choose firmware's zip package
1. Choose mode by pressing `B`


## Bluez commands used by RuuviTag package

Reset bluetooth device:
```sh
$ sudo hciconfig hci0 reset
```

Scan bluetooth devices:
```sh
$ sudo hcitool lescan2 --duplicates --passive
```

Get broadcasted data:
```sh
$ sudo hcidump --raw
```

> NOTE: Scanning must be active in order to get broadcasted data.

## Other useful commands

List bluetooth devices
```sh
$ hcitool dev
```

List processes containing hci in order to find BLE scanning subprocesses
```sh
$ ps aux | grep hci
```

## Example datas from different firmwares and data formats

Kickstarter FW
```python
{'data_format': 2, 'temperature': 24.0, 'humidity': 42.0, 'pressure': 1009.0, 'identifier': None}
```

1.0.1 URL-mode
```python
{'data_format': 4, 'temperature': 26.0, 'humidity': 36.0, 'pressure': 1007.0, 'identifier': 'd'}
```

1.0.1 RAW-mode
```python
{'data_format': 3, 'humidity': 58.0, 'temperature': 24.56, 'pressure': 1009.11, 'acceleration': 1019.803902718557, 'acceleration_x': 344, 'acceleration_y': -8, 'acceleration_z': 960, 'battery': 3283}
```

1.2.12 URL-mode
```python
{'data_format': 4, 'temperature': 25.0, 'humidity': 62.0, 'pressure': 1009.0, 'identifier': 'w'}
```

1.2.12 RAW-mode
```python
{'data_format': 3, 'humidity': 45.5, 'temperature': 25.0, 'pressure': 1008.59, 'acceleration': 1055.12558494238, 'acceleration_x': -11, 'acceleration_y': 12, 'acceleration_z': 1055, 'battery': 3259}
```

2.4.2 RAW-mode
```python
{'data_format': 3, 'humidity': 46.5, 'temperature': 24.81, 'pressure': 1009.93, 'acceleration': 989.23809065361, 'acceleration_x': -48, 'acceleration_y': -12, 'acceleration_z': 988, 'battery': 3175}
```

2.4.2 RAW v2-mode
```python
{'data_format': 5, 'humidity': 44.88, 'temperature': 25.2, 'pressure': 1008.69, 'acceleration': 1034.3616388865164, 'acceleration_x': -64, 'acceleration_y': 28, 'acceleration_z': 1032, 'tx_power': 4, 'battery': 3199, 'movement_counter': 209, 'measurement_sequence_number': 30638, 'mac': 'e62eb92e73e5'}
```

## BLE Broadcast data from RuuviTags

### Bluez

Example data from hcidump:

```sh
> 04 3E 2B 02 01 03 01 C4 C4 37 D3 1E D0 1F 02 01 06 03 03 AA

  FE 17 16 AA FE 10 F6 03 72 75 75 2E 76 69 2F 23 42 47 51 59

  41 4D 71 38 77 98

> 04 3E 25 02 01 03 01 F2 7A 52 FA D4 CD 19 02 01 04 15 FF 99

  04 03 63 18 22 CA 54 FF EC 00 0C 04 0C 0C B5 00 00 00 00 99
```

Example data has 2 broadcasts where '> ' from the beginning and empty spaced are removed:

```
043E2B02010301C4C437D31ED01F0201060303AAFE176AAFE10F6037275752E76692F2342475159414D71387798
```
```
043E2502010301F27A52FAD4CD1902010415FF9904036C180ECA60FC9CFE6801280C91000000009E
```

Data is a hex string.

Data contains 3 parts: `unknown`, `mac` and `payload`

* TODO: What is unknown part?
* MAC is revesed in the data
* Payload is actual sensor data

First data where parts are separated by `_`:
```
043E2B02010301C4_C437D31ED0_1F0201060303AAFE176AAFE10F6037275752E76692F2342475159414D71387798O

MAC = D0:1E:D3:37:C4:C4
PAYLOAD = 1F0201060303AAFE1716AAFE10F6037275752E76692F2342475159414D71387798
```

Second data:
```
043E2502010301_F27A52FAD4CD_1902010415FF9904036C180ECA60FC9CFE6801280C91000000009E

MAC = CD:D4:FA:52:7A:F2
PAYLOAD = 1902010415FF990403631822CA54FFEC000C040C0CB50000000099
```

This handling is done in `ble_communication.py`.

Data format specific handling is in `data_formats.py`.

Data format can be parsed from the payload.

Data format 3 and 5 have Manufacturer Specific Data (FF) / Ruuvi Innovations ltd (9904) / Format 3|5 (03|05)

```
Data format 3: FF990403
Data format 5: FF990405
```
Data format 2 and 4 encode raw data and look for `ruu.vi/#` string from the encoded data.

### Bleson

__TODO: Add examples__

Bleson send data in [bytes object](https://docs.python.org/3/library/stdtypes.html#bytes-objects).

Bleson processes internally mac to an own property, so byte data contains only the payload part of RuuviTag data.

NOTE: Manufacturer Specific Data (FF) is missing from the payload. It is added in the code before deciding the correct data format. This way most of the functions from Bluez version work with the Bleson version.

Bytes is converted to a hex string before data format specific handling.

## Application flow

Get data from Bluetooth device ([BleCommunicationNix.get_datas](https://github.com/ttu/ruuvitag-sensor/blob/f6e62125e9021d0977e8f0d6032f4e74a5a9fed8/ruuvitag_sensor/ble_communication.py#L93))
```
BleCommunicationNix.get_datas
 Start BLE processes
   Reset BLE device (hciconfig hci0 reset)
   Start scanning (hcitool lescan2 --duplicates --passive)
   Start hcidump (hcidump --raw)
 While new data from hcidump
   Get data from hcidump
     While not new line (>)
       Append data
     Yield data
   Parse Mac from data
   If Mac in blacklist
     Continue
   Yield Mac and payload part from data
 Stop BLE processes
   Stop hcitool
   Stop hcidump
```

TODO: Application flow for Bleson

[RuuviTagSensor._get_ruuvitag_datas](https://github.com/ttu/ruuvitag-sensor/blob/f6e62125e9021d0977e8f0d6032f4e74a5a9fed8/ruuvitag_sensor/ruuvi.py#L117)
```
RuuviTagSensor._get_ruuvitag_datas
 While data from BleCommunicationNix.get_datas
   If timeout
     Break
   If runflag set to stopped
     Break
   If whitelist in use and data's Mac not in whitelist
     Continue
   Get data_format and encoded data from data
   If data_format not null
     Use correct data format decoder to decode encoded data
     If decoded data not null
       Yield decoded data
     Else
        Log error
   Else
     Blacklist Mac   
```

[RuuviTagSensor.get_datas](https://github.com/ttu/ruuvitag-sensor/blob/f6e62125e9021d0977e8f0d6032f4e74a5a9fed8/ruuvitag_sensor/ruuvi.py#L99)

```
RuuviTagSensor._get_ruuvitag_datas
 While data from RuuviTagSensor._get_ruuvitag_datas
   Execute callback with data
```

## Executing Unit Tests

Run with nosetests

```sh
$ pip install nose
$ nosetests
```

Run with setup

```sh
$ python setup.py test
```

Execute single test: `nosetests <file>:<Test_Case>.<test_method>`

```sh
$ nosetests test_ruuvitag_sensor:TestRuuviTagSensor.test_convert_data_valid_df3
```

Show print statements on console:
```sh
$ nosetest --nocapture
```

Or use e.g. VS Code to execute and debug tests.

## Exeuting Verification Test

Verification test script executes a set of tests on active RuuviTags. Tests require at least one active RuuviTag and Python 2.7 and 3.x.

```sh
$ chmod +x verification.sh
$ sudo ./verification.sh
```

Run verification for the package from pypi

```sh
$ sudo ./verification.sh pypi
```

## Run long duration tests

Test will create new BLE scanning subprocesses on each get_data_for_sensors-method call (approx every 5sec)

```python
from datetime import datetime
from ruuvitag_sensor.ruuvi import RuuviTagSensor

import ruuvitag_sensor.log

ruuvitag_sensor.log.enable_console()

macs = []

while True:
   datas = RuuviTagSensor.get_data_for_sensors(macs, search_duratio_sec=5)
   print(datetime.utcnow().isoformat())
   print(datas)
```

Create new connections with 1 minute interval

```python
# Use sleep from time to pause the execution
import time
# Add after print(datas)
time.sleep(60)
```

Normal scanning function is good for running normal long duration tests without abusing BLE scanning process as it will just initialize the connection once in the beginning
```sh
$ sudo python3 ruuvitag_sensor -s
```

## Randomly create bad BLE broadcast data

Add to `ble_communication.py`:
```python
import random
```

Replace from `BleCommunicationNix get_datas`-method
```python
data = line[26:]
# with this line
data = line[26:] if random.randint(1,10) != 10 else line[25:] + 'not_valid'
```

## Error cases

Error from command `hciconfig hci0 reset`
```
Can't init device hci0: Operation not possible due to RF-kill (132)
```

Fix:
```sh
$ rfkill unblock all
```

Error from command `hcitool lescan --duplicates`
```
Set scan parameters failed: Input/output error
```

Fix:
```sh
$ hciconfig hci0 reset
```

## Relese a new version

### Build release

https://packaging.python.org/en/latest/tutorials/packaging-projects/#generating-distribution-archives

```sh
$ python -m build
```

### Test in testpypi

Upload to test pypi to verify that descriptions etc. are correct

https://test.pypi.org/project/ruuvitag-sensor/

https://twine.readthedocs.io/en/stable/#using-twine
```sh
$ twine upload -r testpypi dist/*
```

### Release a new version

1. Update version and push to master ([example](https://github.com/ttu/ruuvitag-sensor/commit/a141e73952949a37bdcfd5e2902968135ed48146)). 
2. Update Tags
```sh
$ git tag x.x.x
$ git push origin --tags
```
3. Upload new version to pypi
```
$ twine upload dist/*
```
