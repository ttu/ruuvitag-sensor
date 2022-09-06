import io
from setuptools import setup

import ruuvitag_sensor


with io.open('README.md', encoding='utf-8') as f:
    readme = f.read()

setup(name='ruuvitag_sensor',
      version=ruuvitag_sensor.__version__,
      description='Find RuuviTag sensor beacons, get and encode data from '
                  'selected sensors',
      long_description=readme,
      long_description_content_type="text/markdown",
      url='https://github.com/ttu/ruuvitag-sensor',
      download_url='https://github.com/ttu/ruuvitag-sensor/tarball/' +  # noqa: W504
                   ruuvitag_sensor.__version__,
      author='Tomi Tuhkanen',
      author_email='tomi.tuhkanen@iki.fi',
      platforms='any',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3'
      ],
      keywords='RuuviTag BLE',
      setup_requires=['wheel'],
      install_requires=[
          'reactivex',
          'ptyprocess;platform_system=="Linux"',
          'mypy-extensions;python_version<"3.8"'
      ],
      license='MIT',
      packages=['ruuvitag_sensor', 'ruuvitag_sensor.adapters'],
      include_package_data=True,
      zip_safe=True)
