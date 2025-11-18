import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest

from ruuvitag_sensor.adapters.dummy import BleCommunicationAsyncDummy, BleCommunicationDummy
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvi_types import MacAndRawData
from ruuvitag_sensor.ruuvitag import RuuviTagAsync


@pytest.mark.asyncio
class TestRuuviTagSensorAsync:
    async def _get_first_data(self, _mac, _bt_device):
        await asyncio.sleep(0)
        # https://ruu.vi/#AjwYAMFc
        data = "043E2A0201030157168974A5F41E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD"
        return data[26:]

    async def _get_data(self, _blacklist=None, _bt_device="") -> AsyncGenerator[MacAndRawData, None]:
        if _blacklist is None:
            _blacklist = []

        tag_data = [
            ("EB:A5:D1:02:CE:68", "1c1bFF99040513844533c43dffe0ffd804189ff645fcffeba5d102ce68"),
            ("CD:D4:FA:52:7A:F2", "1c1bFF990405128a423bc45fffd8ff98040cafd6497a83cdd4fa527af2"),
            ("EC:4D:A7:95:08:6B", "1c1bFF9904050d3f5306c4df0024ffe404108f562787f1ec4da795086b"),
            ("CE:D6:05:F5:17:AA", "1c1bFF990405118f60bcc7f900880000fc0c813624238fc57d89639eb9a6"),
        ]

        for data in tag_data:
            yield data

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationAsyncDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_get_data_async(self):
        gener = RuuviTagSensor.get_data_async()
        data = [received async for received in gener]

        assert len(data) == 4

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationAsyncDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_get_data_async_with_macs(self):
        macs = ["EB:A5:D1:02:CE:68", "EC:4D:A7:95:08:6B"]
        gener = RuuviTagSensor.get_data_async(macs)
        data = [received async for received in gener]

        assert len(data) == 2

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationAsyncDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_find_ruuvitags_async_with_bleak(self):
        """Tests to see if MAC and the state of the sensors are returned for Bleak enabled request."""
        tags = await RuuviTagSensor.find_ruuvitags_async()

        assert len(tags) == 4

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_find_ruuvitags_async_without_bleak(self):
        """Tests to see if exception is raised for non-Bleak enabled request.

        Async communication is supported only for BLE devices of subclass `BleCommunicationAsync`. This
        test forces a non-compatible BLE device type (BleCommunicationDummy subclass) to raise RuntimeError.
        """
        with pytest.raises(RuntimeError, match="Async BLE adapter required"):
            _ = await RuuviTagSensor.find_ruuvitags_async()

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationAsyncDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_first_data", _get_first_data)
    async def test_tag_async_update_is_valid(self):
        tag = RuuviTagAsync("48:2C:6A:1E:59:3D")

        state = tag.state
        assert state == {}

        state = await tag.update()
        assert state["temperature"] == 24
        assert state["pressure"] == 995
        assert state["humidity"] == 30

    @patch("ruuvitag_sensor.ruuvi.ble", BleCommunicationAsyncDummy())
    @patch("ruuvitag_sensor.adapters.dummy.BleCommunicationAsyncDummy.get_data", _get_data)
    async def test_get_data_for_sensors(self):
        macs = ["EB:A5:D1:02:CE:68", "CD:D4:FA:52:7A:F2", "CE:D6:05:F5:17:AA"]
        data = await RuuviTagSensor.get_data_for_sensors_async(macs, 4)
        assert len(data) == 3
        assert "EB:A5:D1:02:CE:68" in data
        assert "CD:D4:FA:52:7A:F2" in data
        assert "CE:D6:05:F5:17:AA" in data
        assert data["EB:A5:D1:02:CE:68"]["temperature"] == 24.98
        assert data["CD:D4:FA:52:7A:F2"]["temperature"] == 23.73
        assert data["CE:D6:05:F5:17:AA"]["rssi"] == -90
