#!/bin/bash

rm -rf venv_py3
rm -rf venv_py2

python3 -m venv venv_py3
source venv_py3/bin/activate
if [ "$1" = "pypi" ]; then
  python3 -m pip install ruuvitag_sensor
else
  python3 -m pip install -e .
fi
python3 verification.py
ret=$?
if [ $ret -ne 0 ]; then
  echo 'Python 3 verification failed'
  rm -rf venv_py3
  exit 1
fi
deactivate
rm -rf venv_py3

virtualenv --python=/usr/bin/python2.7 venv_py2
source venv_py2/bin/activate
if [ "$1" = "pypi" ]; then
  pip install ruuvitag_sensor
else
  pip install -e .
fi
python verification.py
ret=$?
if [ $ret -ne 0 ]; then
  echo 'Python 2.7 verification failed'
  rm -rf venv_py2
  exit 1
fi
deactivate
rm -rf venv_py2

echo '----------------------'
echo 'VERIFICATION COMPLETED'
