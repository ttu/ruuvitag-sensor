# Raspbian

RuuviTag is a Bluetooth Low Energy device. 
Bluetooth 4.0 support is required from the Bluetooth adapter. Raspberry Pi 3 as well as Pi Zero W have integrated Bluetooth which support BLE devices. For older models a Bluetooth adapter is required.

Tested with Raspbian Jessie 2017-01-11 and '4.9.35-v7+ #1014 SMP Fri Jun 30 14:47:43 BST 2017', and '4.14.79-v7+ #1159 SMP Sun Nov 4 17:50:20 GMT 2018 armv7l GNU/Linux'

Offical startup  https://www.raspberrypi.org/documentation/configuration/raspi-config.md

Summerized here:

### Start the pi

Plug display and keyboard

Open Terminal

### Enable SSH (optional)

Open raspi-config to enable SSH
```sh
$ sudo raspi-config
```
Select Hostname and give your pi a name.

You may want to Select Localisation Options Set up language and regional settings(timezone) to match your location

Select Interface Options 

 SSH and enable ssh server (Secure Shell command line
 
<!-- use the name not an IP address
Check IP-address
```sh
$ ip a
```
Expect something like 192.168.1.x (can be found after eth0:, inet )-->
Now you can either connect to raspberry pi over the network with SSH (For example use Putty from windows) or continue using current terminal.

Use these login credentials
```
username: pi 
password: raspberry
```

### Update the System

Update package indexes and upgrade installed packages. 
apt-get is rather verbose and how long it takes depends on what needs to be updated.
```sh
$ sudo apt-get update &&  sudo apt-get dist-upgrade && echo +++ upgrade successful +++
```

### Bluetooth

List Bluetooth devices and verify that hci0 is on the list
```sh
$ hcitool dev
```
Expect output similar to
```sh
Devices:
	hci0	B8:27:EB:96:64:43
```

If no devices are listed, reboot and check again
```sh
$ reboot
```

If still nothing, install Bluetooth again
```sh
$ sudo apt-get install bluetooth bluez blueman
$ reboot
```

### Update Python 3 version (optional)

You might want to update default version of Python 3 to a newer version. Newer version must be installed from the sources. This will take around 20min to complete.

Install dependencies so SSL will work with newly compiled pip (not sure if all of these are needed)
```sh
$ sudo apt-get install libbz2-dev liblzma-dev libsqlite3-dev libncurses5-dev libgdbm-dev zlib1g-dev libreadline-dev libssl-dev tk-dev
```

This example installs version 3.6.0
```sh
$ wget https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tgz
$ tar xzvf Python-3.6.0.tgz
$ cd Python-3.6.0/
$ ./configure
$ make -j2
$ sudo make install
# to preserve the existing custom python installations (e.g. having python3.6 installed and want python3.7 on the side)
# $ sudo make altinstall
$ reboot
```

### Install ruuvitag-sensor package

<!-- seems extraenous, but that's up to you
leave in as a comment may be of interest later
In this example we use default installed version of Python 3, which is 3.4.2. 
Raspbian has also Python 2.7 installed, but it is already 2017, so we will use Python 3. You can check current version with version option. If you want to use Python 2, install also `sudo apt-get install python-dev`. Python developer package is already installed for Python 3
```sh
$ python3 --version
```
-->
Ruuvitag-sensor package requires bluez and bluez-hcidump. 
Bluez is the Linux Bluetooth system and allows a Raspberry Pi to communicate with Bluetooth classic and Bluetooth low energy (LE) devices and is included with Raspbian. 
Hcidump is a tool which prints data broadcasted by Bluetooth devices to console and needs to be installed.
```sh
$ sudo apt-get install bluez-hcidump && echo +++ install successful +++
```
Expect the usual verbose output from apt-get.

Upgrade setuptools
```sh
$ sudo pip3 install --upgrade setuptools
```

Install ruuvitag-sensor package from the Python Package Index (PyPI) with pip (Python package management system). Because we are using Python 3, install ruuvitag-sensor package with pip3. Add --user to install for current user
```sh
$ pip3 install --user ruuvitag-sensor
```
This library includes a command line utility.

Try displaying the help. 
```sh
$ python3 ~/.local/lib/python3.4/site-packages/ruuvitag_sensor --help
```
Expect
```sh
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
 If this fails with a Traceback, change the path to match Python's minor version, i.e. if you updated Python to version 3.6. then path is ~/.local/lib/python3.6/...

Make an alias if you choose
```sh
$ alias ruuvitag='python3 ~/.local/lib/python3.4/site-packages/ruuvitag_sensor'
```

Try to find all tags
```sh
$ ruuvitag -f
```
After several seconds, expect something like
```sh
F2:C0:C6:43:AD:03
{'pressure': 1003.0, 'identifier': 'N', 'temperature': 20.0, 'humidity': 52.0}
E9:38:3F:DD:20:BC
{'pressure': 1004.0, 'identifier': 'r', 'temperature': 22.0, 'humidity': 100.0}
D3:51:78:72:EC:0F
{'pressure': 1003.0, 'identifier': 's', 'temperature': 11.0, 'humidity': 60.0}
```
This continues waiting for additional tags to be detected until interrupted with ^C.


Open nano editor and create test script tag_test.py
```sh
$ nano tag_test.py
```

Add this content. Exit with Ctrl-X and select Y to save
```python
import ruuvitag_sensor
from ruuvitag_sensor.log import log
from ruuvitag_sensor.ruuvi import RuuviTagSensor

ruuvitag_sensor.log.enable_console()

RuuviTagSensor.find_ruuvitags()
```

Execute script just created. Expect the same result as from find all tags executed from the command line.
```sh
$ python3 tag_test.py
```

Now you are all set! 

Remember to check examples from the [examples](https://github.com/ttu/ruuvitag-sensor/tree/master/examples) directory.
