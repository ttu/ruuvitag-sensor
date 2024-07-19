#!/bin/bash

rm -rf .venv_py

python -m venv .venv_py
source .venv_py/bin/activate
if [ "$1" = "pypi" ]; then
  python -m pip install ruuvitag_sensor
else
  python -m pip install -e .
fi

file_to_run="verification_async.py"

if [ "$RUUVI_BLE_ADAPTER" = "bleson" ]; then
  python -m pip install git+https://github.com/TheCellule/python-bleson
  file_to_run="verification.py"
elif [ "$RUUVI_BLE_ADAPTER" = "bluez" ]; then
  file_to_run="verification.py"
fi

python $file_to_run

ret=$?
if [ $ret -ne 0 ]; then
  echo 'Python 3 verification failed'
  rm -rf .venv_py
  exit 1
fi
deactivate
rm -rf .venv_py

echo '----------------------'
echo 'VERIFICATION COMPLETED'
