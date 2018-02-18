#!/bin/bash

rm -rf venv_py3
rm -rf venv_py2

python3 -m venv venv_py3
source venv_py3/bin/activate
pip3 install -e .
python3 verification.py
ret=$?
if [ $ret -ne 0 ]; then
     echo 'Python 3 verification failed'
     return 1
fi
deactivate

virtualenv --python=/usr/bin/python2.7 venv_py2
source venv_py2/bin/activate
pip install -e .
python verification.py
ret=$?
if [ $ret -ne 0 ]; then
     echo 'Python 2.7 verification failed'
     return 1
fi
deactivate


echo '----------------------'
echo 'VERIFICATION COMPLETED'
