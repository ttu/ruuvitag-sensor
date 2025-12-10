import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from bleak.backends.scanner import AdvertisementData, BLEDevice
from pytest import approx

from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvi_types import SensorData5, SensorData6


def create_mock_advertisement_data(manufacturer_data: dict[int, bytes], rssi: int = -70) -> AdvertisementData:
    return AdvertisementData(
        local_name="",
        manufacturer_data=manufacturer_data,
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=rssi,
        platform_data=(),
    )


def assert_sensor_data_equal(actual: dict, expected: dict, float_tolerance: float = 0.1) -> None:
    data_format = expected["data_format"]

    if data_format == 5:
        assert actual["data_format"] == 5
        assert actual["temperature"] == approx(expected["temperature"], abs=float_tolerance)
        assert actual["humidity"] == approx(expected["humidity"], abs=float_tolerance)
        assert actual["pressure"] == approx(expected["pressure"], abs=1.0)
        assert actual["acceleration"] == approx(expected["acceleration"], abs=float_tolerance)
        assert actual["acceleration_x"] == expected["acceleration_x"]
        assert actual["acceleration_y"] == expected["acceleration_y"]
        assert actual["acceleration_z"] == expected["acceleration_z"]
        assert actual["tx_power"] == expected["tx_power"]
        assert actual["battery"] == expected["battery"]
        assert actual["movement_counter"] == expected["movement_counter"]
        assert actual["measurement_sequence_number"] == expected["measurement_sequence_number"]
        assert actual["mac"] == expected["mac"]
        if "rssi" in expected:
            assert actual["rssi"] == expected["rssi"]

    elif data_format == 6:
        assert actual["data_format"] == 6
        assert actual["temperature"] == approx(expected["temperature"], abs=float_tolerance)
        assert actual["humidity"] == approx(expected["humidity"], abs=float_tolerance)
        assert actual["pressure"] == approx(expected["pressure"], abs=1.0)
        assert actual["pm_2_5"] == approx(expected["pm_2_5"], abs=float_tolerance)
        assert actual["co2"] == expected["co2"]
        assert actual["voc"] == expected["voc"]
        assert actual["nox"] == expected["nox"]
        assert actual["luminosity"] == approx(expected["luminosity"], abs=float_tolerance)
        assert actual["measurement_sequence_number"] == expected["measurement_sequence_number"]
        assert actual["calibration_in_progress"] == expected["calibration_in_progress"]
        assert actual["mac"] == expected["mac"]
    else:
        raise ValueError(f"Unsupported data format: {data_format}")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_data",
    [
        # DF5 test data: Temperature: 24.30°C, Humidity: 53.49%, Pressure: 1000.44 hPa
        # MAC: CB:B8:33:4C:88:4F
        # Based on test data from test_df5_decoder.py
        (
            bytes.fromhex("0512FC5394C37C0004FFFC040CAC364200CDCBB8334C884F"),  # raw_data
            SensorData5(
                data_format=5,
                mac="cbb8334c884f",  # MAC from payload (lowercase, no colons)
                temperature=24.30,
                humidity=53.49,
                pressure=1000.44,
                acceleration=1036.015443900331,
                acceleration_x=4,
                acceleration_y=-4,
                acceleration_z=1036,
                tx_power=4,
                battery=2977,
                movement_counter=66,
                measurement_sequence_number=205,
                rssi=-70,
            ),
            "CB:B8:33:4C:88:4F",  # advertised_mac (with colons)
        ),
        # DF6 test data: Temperature: 29.5°C, Humidity: 55.3%, Pressure: 1011.02 hPa
        # MAC: 4C:88:4F
        # Based on test data from test_df6_decoder.py
        (
            bytes.fromhex("06170C5668C79E007000C90501D9FFCD004C884F"),  # raw_data
            SensorData6(
                data_format=6,
                mac="4c884f",  # MAC from payload (lowercase, no colons)
                temperature=29.5,
                humidity=55.3,
                pressure=1011.02,
                pm_2_5=11.2,
                co2=201,
                voc=10,
                nox=2,
                luminosity=13026.67,
                measurement_sequence_number=205,
                calibration_in_progress=False,
            ),
            "AA:BB:CC:4C:88:4F",  # advertised_mac (full 6-byte MAC with colons)
        ),
    ],
)
@patch("ruuvitag_sensor.ruuvi.ble", new_callable=lambda: BleCommunicationBleak())
@patch("ruuvitag_sensor.adapters.bleak_ble.queue", new_callable=lambda: asyncio.Queue())
@patch("ruuvitag_sensor.adapters.bleak_ble._get_scanner")
async def test_get_data_async_with_data_format(mock_get_scanner, _test_queue, _mock_ble, test_data):
    raw_data, expected, advertised_mac = test_data

    mock_device = BLEDevice(advertised_mac, "RuuviTag", {})
    mock_ad_data = create_mock_advertisement_data({1177: raw_data}, expected.get("rssi", -70))

    # Track the callback that will be passed to the scanner
    captured_callback = None

    mock_scanner = AsyncMock()
    mock_scanner.start = AsyncMock()
    mock_scanner.stop = AsyncMock()

    def mock_get_scanner_side_effect(detection_callback, _bt_device: str = ""):
        nonlocal captured_callback
        captured_callback = detection_callback
        return mock_scanner

    mock_get_scanner.side_effect = mock_get_scanner_side_effect

    # Start the async generator
    data_gen = RuuviTagSensor.get_data_async()

    # Start iteration to trigger scanner.start() and capture callback
    gen_task = asyncio.create_task(data_gen.__anext__())

    # Wait for scanner to start and callback to be captured
    await asyncio.sleep(0.1)

    # Simulate device detection
    await captured_callback(mock_device, mock_ad_data)

    # Get the first data point (should be decoded sensor data)
    mac, sensor_data = await asyncio.wait_for(gen_task, timeout=2.0)

    assert mac == advertised_mac
    assert_sensor_data_equal(sensor_data, expected)

    await data_gen.aclose()
