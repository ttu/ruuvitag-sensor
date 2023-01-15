import sys
from typing import Tuple
from unittest.mock import patch

import pytest

from ruuvitag_sensor.adapters.dummy import BleCommunicationAsyncDummy, BleCommunicationDummy
from ruuvitag_sensor.ruuvi import RuuviTagSensor

# pylint: disable=unused-argument


@pytest.mark.skipif(sys.version_info < (3, 8), reason="patch doesn't work correctly on 3.7")
@pytest.mark.asyncio
class TestRuuviTagSensorAsync:
    async def _get_data(self, blacklist=[], bt_device="") -> Tuple[str, str]:
        tag_data = [
            ("EB:A5:D1:02:CE:68", "1c1bFF99040513844533c43dffe0ffd804189ff645fcffeba5d102ce68"),
            ("CD:D4:FA:52:7A:F2", "1c1bFF990405128a423bc45fffd8ff98040cafd6497a83cdd4fa527af2"),
            ("EC:4D:A7:95:08:6B", "1c1bFF9904050d3f5306c4df0024ffe404108f562787f1ec4da795086b"),
        ]

        for data in tag_data:
            yield data

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationAsyncDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_get_data_async(self):
        data = []
        gener = RuuviTagSensor.get_data_async()
        async for received in gener:
            data.append(received)

        assert len(data) == 3

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationAsyncDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_get_data_async_with_macs(self):
        data = []
        macs = ["EB:A5:D1:02:CE:68", "EC:4D:A7:95:08:6B"]
        gener = RuuviTagSensor.get_data_async(macs)
        async for received in gener:
            data.append(received)

        assert len(data) == 2

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationAsyncDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_find_ruuvitags_async_with_bleak(self):
        """Tests to see if MAC and the state of the sensors are returned for Bleak enabled request."""
        tags = await RuuviTagSensor.find_ruuvitags_async()

        assert len(tags) == 3

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_find_ruuvitags_async_without_bleak(self):
        """Tests to see if exception is raised for non-Bleak enabled request.

        Async communication is supported only for BLE devices of subclass `BleCommunicationAsync`. This
        test forces a non-compatible BLE device type (BleCommunicationDummy subclass) to raise Exception.
        """
        with pytest.raises(Exception):
            _ = await RuuviTagSensor.find_ruuvitags_async()
