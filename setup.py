import io
from setuptools import setup

import ruuvitag_sensor


with io.open('README.md', encoding='utf-8') as f:
    readme = f.read()

setup(name='ruuvitag_sensor',
      version=ruuvitag_sensor.__version__,
      description='Find RuuviTag sensor beacons, get and encode data from ' +
                  'selected sensors',
      long_description=readme,
      long_description_content_type="text/markdown",
      url='https://github.com/ttu/ruuvitag-sensor',
      download_url='https://github.com/ttu/ruuvitag-sensor/tarball/' +
                   ruuvitag_sensor.__version__,
      author='Tomi Tuhkanen',
      author_email='tomi.tuhkanen@iki.fi',
      platforms='any',
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
      ],
      keywords='RuuviTag BLE',
      install_requires=[
          'rx<3',
          'futures;python_version<"3.3"',
          'ptyprocess;platform_system=="Linux"'
      ],
      license='MIT',
      packages=['ruuvitag_sensor', 'ruuvitag_sensor.adapters'],
      include_package_data=True,
      tests_require=[
          'nose',
          'mock'
      ],
      test_suite='nose.collector',
      zip_safe=True)
