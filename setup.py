import sys
from setuptools import setup

import ruuvitag_sensor

if sys.version_info >= (3, 5):
    sys.exit("Only Python version < 3.5 is supported")

setup(name='ruuvitag_sensor',
      version=ruuvitag_sensor.__version__,
      description='Find RuuviTag sensor beacons and get data from selected ' +
                  'sensor and decode data from eddystone url',
      url='https://github.com/ttu/ruuvitag-sensor',
      author='Tomi Tuhkanen',
      author_email='tomi.tuhkanen@iki.fi',
      install_requires=[
        "base91",
      ]+([] if "win" in sys.platform else ["gattlib"]),
      license='MIT',
      packages=['ruuvitag_sensor'],
      include_package_data=True,
      tests_require=['nose'],
      test_suite='nose.collector',
      zip_safe=True)
