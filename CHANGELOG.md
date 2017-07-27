## Changelog

### [Unreleased]
* Blacklist MACs of BLE devices that are not RuuviTag sensors
* Breaking change code refactoring if used RuuviTagSensor as an object or RunFlag
    * Split RuuviTagSensor class to static functions (RuuviTagSensor) and RuuviTag sensor object (RuuviTag)
    * Move RunFlag to common.py

## [0.7.0] - 2017-06-28
* Fix module logging
* Replace print-functions with logging
* Log to console disabled by default

## [0.6.0] - 2017-05-05
* Support for Data Format 3 and 4
* Fix data decoder Python2 support

## [0.5.0] - 2017-03-01
* RuuviTagReactive: reactive wrapper and background process for RuuviTagSensor get_datas 
* Fix for hcitool and hcidump subprocess kill
* Fix data decode. Use minus and underscore as altchars as encoding is url-safe

## [0.4.0] - 2017-02-19
* get_datas function for handling RuuviTag broadcasts with callback function
* MAC list to optional in get_data_for_sensors function

## [0.3.4] - 2017-02-01
* Fix temperature decimal calculation 

## [0.3.3] - 2017-01-31
* Use subprocess.DEVNULL starting with Python 3.3

## [0.3.2] - 2017-01-30
* Use psutil to find correct process to kill

## [0.3.1] - 2017-01-29
* Fix for hcitool subprocess kill

## [0.3.0] - 2017-01-29
* Get latest data for specified sensors 
* Accept ruu.vi/# and r/ as RuuviTag datas in conversion

## [0.2.2] - 2017-01-03
* Python 2.7 support

## [0.2.1] - 2017-01-01
* Use base64 encoding to suupport new Weather Station firmware 

## [0.2] - 2016-12-31
* Find RuuviTags functionality
* Change gattlib to BlueZ (use hcitool and hcidump)
