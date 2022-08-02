#!/bin/bash

rm -rf venv_py

# If python command is for 2.7, replace next line with: python3 -m venv venv_py
python -m venv venv_py
source venv_py/bin/activate
if [ "$1" = "pypi" ]; then
  python -m pip install ruuvitag_sensor
else
  python -m pip install -e .
fi

if [ "$RUUVI_BLE_ADAPTER" = "Bleson" ]; then
  python -m pip install git+https://github.com/TheCellule/python-bleson
fi

python verification.py
ret=$?
if [ $ret -ne 0 ]; then
  echo 'Python 3 verification failed'
  rm -rf venv_py
  exit 1
fi
deactivate
rm -rf venv_py

echo '----------------------'
echo 'VERIFICATION COMPLETED'
