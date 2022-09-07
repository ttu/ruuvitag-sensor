from typing import Tuple
from unittest.mock import patch
import pytest

"""
NOTE: Execute tests manually. These are not part of CI
Setting env variables for CI or READTHEDOCS didn't work with Travis

# https://github.com/hbldh/bleak/discussions/475

.tox/py37-basic_linux/lib/python3.7/site-packages/bleak/__init__.py:41: in <module>
    if not _on_ci and not check_bluez_version(5, 43):
.tox/py37-basic_linux/lib/python3.7/site-packages/bleak/backends/bluezdbus/__init__.py:17: \
 in check_bluez_version
    p = subprocess.Popen(["bluetoothctl", "--version"], stdout=subprocess.PIPE)

FileNotFoundError: [Errno 2] No such file or directory: 'bluetoothctl': 'bluetoothctl'
"""

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak

# pylint: disable=line-too-long,unused-argument


@pytest.mark.skip(reason="Doesn't work with CI")
@patch('ruuvitag_sensor.ruuvi.ble', BleCommunicationBleak())
class TestRuuviTagSensorAsync:

    async def _get_data(self, blacklist=[], bt_device='') -> Tuple[str, str]:
        tag_data = [
            ('EB:A5:D1:02:CE:68', '1c1bFF99040513844533c43dffe0ffd804189ff645fcffeba5d102ce68'),
            ('CD:D4:FA:52:7A:F2', '1c1bFF990405128a423bc45fffd8ff98040cafd6497a83cdd4fa527af2'),
            ('EC:4D:A7:95:08:6B', '1c1bFF9904050d3f5306c4df0024ffe404108f562787f1ec4da795086b')
        ]

        for data in tag_data:
            yield data

    @patch('ruuvitag_sensor.adapters.bleak_ble.BleCommunicationBleak.get_data', _get_data)
    @pytest.mark.asyncio
    async def test_get_data_async(self):
        data = []
        gener = RuuviTagSensor.get_data_async()
        async for received in gener:
            data.append(received)

        assert len(data) == 3

    @patch('ruuvitag_sensor.adapters.bleak_ble.BleCommunicationBleak.get_data', _get_data)
    @pytest.mark.asyncio
    async def test_get_data_async_with_macs(self):
        data = []
        macs = ['EB:A5:D1:02:CE:68', 'EC:4D:A7:95:08:6B']
        gener = RuuviTagSensor.get_data_async(macs)
        async for received in gener:
            data.append(received)

        assert len(data) == 2
