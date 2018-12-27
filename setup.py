import io
from setuptools import setup
import ruuvitag_sensing

with io.open('README.md', encoding="utf-8") as f:
    readme = f.read()

setup(
    name='ruuvitag_sensing',
    version=ruuvitag_sensing.__version__,
    description='Find RuuviTag sensor beacons and get data from selected ' 
    + 'sensor and decode data from eddystone url',
    long_description=readme,
    url='https://github.com/musterp/ruuvitag-sensing',
    download_url='https://github.com/musterp/ruuvitag-sensing/tarball/' 
    + ruuvitag_sensing.__version__,
    author='Tomi Tuhkanen, Pascal Muster',
    author_email='tomi.tuhkanen@iki.fi',
    platforms='Linux, Unix',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ],
    keywords='RuuviTag BLE Sensing',
    install_requires=[
        'rx',
        'psutil;platform_system=="Linux"',
        'futures;python_version<"3.3"',
        'ptyprocess;platform_system=="Linux"'
    ],
    license='MIT',
    packages=['ruuvitag_sensing'],
    include_package_data=True,
    tests_require=[
        'nose',
        'mock'
    ],
    test_suite='nose.collector',
    zip_safe=True)
    
