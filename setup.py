import sys
from setuptools import setup

setup(name='ruuvitag_sensor',
      version='0.1',
      description='Get data from selected RuuviTag sensor beacon and decode sensor data from eddystone url',
      url='',
      author='Tomi Tuhkanen',
      author_email='tomi.tuhkanen@iki.fi',
      install_requires=[
        "base91",
      ]+([] if "win" in sys.platform else ["gattlib"]),
      license='MIT',
      packages=['ruuvitag_sensor'],
      include_package_data=True,
      setup_require=['nose'],
      tests_require=['nose'],
      test_suite='nose.collector',
      zip_safe=False)
