import sys
from setuptools import setup

import ruuvitag_sensor

try:
    import pypandoc
    readme = pypandoc.convert('README.md', 'rst')
    readme = readme.replace("\r", "")
except ImportError:
    import io
    with io.open('README.md', encoding="utf-8") as f:
        readme = f.read()

setup(name='ruuvitag_sensor',
      version=ruuvitag_sensor.__version__,
      description='Find RuuviTag sensor beacons and get data from selected ' +
                  'sensor and decode data from eddystone url',
      long_description=readme,
      url='https://github.com/ttu/ruuvitag-sensor',
      download_url='https://github.com/ttu/ruuvitag-sensor/tarball/' +
                   ruuvitag_sensor.__version__,
      author='Tomi Tuhkanen',
      author_email='tomi.tuhkanen@iki.fi',
      platforms='any',
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
      ],
      keywords='RuuviTag BLE',
      install_requires=[]+(['psutil', 'rx'] if "linux" in sys.platform else ['rx']),
      license='MIT',
      packages=['ruuvitag_sensor'],
      include_package_data=True,
      tests_require=['nose'],
      test_suite='nose.collector',
      zip_safe=True)
