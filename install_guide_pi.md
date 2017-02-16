# Raspbian

Tested with Raspbian Jessie 2017-01-11. 

RuuviTag is a Bluetooth Low Energy device, so Bluetooth 4.0 support is required from the Bluetooth adapter. Raspberry Pi 3 has integrated Bluetooth which support BLE devices. For older models Bluetooth adapter is required.

### Start

Plug display and keyboard

Connect to Wifi

Open Terminal

### Enable SSH (optional)

Open raspi-config to enable SSH
```sh
$ sudo raspi-config
```

Select 7 advanced options and A4 SSH and enable ssh server

Check IP-address
```sh
$ ip a
```

Pretty likely it is something like 192.168.1.x (can be found ~4th row from the bottom)

Now you can either connect to raspberry with SSH (e.g. Putty from windows) or continue using current terminal

If you connect from SSH, use these login credentials
```
username: pi 
password: raspberry
```

### Update System

Update package indexes and upgrade installed packages. This will take some minutes
```sh
$ sudo apt-get update
$ sudo apt-get upgrade
```

### Bluetooth

List Bluetooth devices and check that you can see device hci0 on the list
```sh
$ hcitool dev
```

If not, try to reboot and check again
```sh
$ reboot
```

If still nothing, install Bluetooth again
```sh
$ sudo apt-get install bluetooth bluez blueman
$ reboot
```

### Update Python 3 version (optional)

You might want't to update default version of Python 3 to a newer version. Newer version must be installed from the sources. This will take around 20min to complete.

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
$ make
$ sudo make install
$ reboot
```

### Install ruuvitag-sensor package

In this example we use default installed version of Python 3, which is 3.4.2. Raspbian has also Python 2.7 installed, but it is already 2017, so we will use Python 3. You can check current version with version option. If you want to use Python 2, install also `sudo apt-get install python-dev`. Python developer package is already installed for Python 3
```sh
$ python3 --version
```

Ruuvitag-sensor package requires bluez and bluez-hcidump. Bluez is the Linux Bluetooth system and allows a Raspberry Pi to communicate with Bluetooth classic and Bluetooth low energy (LE) devices. Hcidump is a tool which prints data broadcasted by Bluetooth devices to console. Bluez is already installed on Raspbian, so install only bluez-hcidump
```sh
$ sudo apt-get install bluez-hcidump
```

Install ruuvitag-sensor package from the Python Package Index (PyPI) with pip (Python package management system). Because we are using Python 3, install ruuvitag-sensor package with pip3. Add user option to install for current user
```sh
$ pip3 install --user ruuvitag-sensor
```

Try installed package from command line. Should show help from ruuvitag_sensor. If not, change the minor version from the path to match Python's minor version, e.g. if you updated Python to version 3.6. then path is /home/pi/.local/lib/python3.6/...
```sh
$ python3 /home/pi/.local/lib/python3.4/site-packages/ruuvitag_sensor -h
```

Try to find all tags from command line
```sh
$ python3 /home/pi/.local/lib/python3.4/site-packages/ruuvitag_sensor -f
```

Open nano editor and create test script tag_test.py
```sh
$ nano tag_test.py
```

Add this content. Exit with Ctrl-X and select Y to save
```python
from ruuvitag_sensor.ruuvi import RuuviTagSensor

RuuviTagSensor.find_ruuvitags()
```

Execute script we just created. Should get the same result as from find all tags that was executed from the command line.
```sh
$ python3 tag_test.py
```

Now you are all set! Remember to check examples from the [examples](https://github.com/ttu/ruuvitag-sensor/tree/master/examples) directory.