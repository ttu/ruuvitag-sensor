from typing import Tuple
from unittest.mock import patch
import pytest
import os
os.environ['RUUVI_BLE_ADAPTER'] = 'bleak'

from ruuvitag_sensor.ruuvi import RuuviTagSensor

# pylint: disable=line-too-long,no-self-use,unused-argument

# pytest
# pytest-asyncio

class TestRuuviTagSensorAsync:

    async def _get_datas(self, blacklist=[], bt_device='') -> Tuple[str, str]:
        datas = [
            ('EB:A5:D1:02:CE:68', '1c1bFF99040513844533c43dffe0ffd804189ff645fcffeba5d102ce68'),
            ('CD:D4:FA:52:7A:F2', '1c1bFF990405128a423bc45fffd8ff98040cafd6497a83cdd4fa527af2'),
            ('EC:4D:A7:95:08:6B', '1c1bFF9904050d3f5306c4df0024ffe404108f562787f1ec4da795086b')
        ]

        for data in datas:
            yield data

    @patch('ruuvitag_sensor.adapters.bleak_ble.BleCommunicationBleak.get_datas', _get_datas)
    @pytest.mark.asyncio
    async def test_get_datas(self):
        datas = []
        gener = RuuviTagSensor.get_datas_async()
        async for data in gener:
            datas.append(data)

        assert len(datas) == 3

    @patch('ruuvitag_sensor.adapters.bleak_ble.BleCommunicationBleak.get_datas', _get_datas)
    @pytest.mark.asyncio
    async def test_get_datas_with_macs(self):
        datas = []
        macs = ['EB:A5:D1:02:CE:68', 'EC:4D:A7:95:08:6B']
        gener = RuuviTagSensor.get_datas_async(macs)
        async for data in gener:
            datas.append(data)

        assert len(datas) == 2
