import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.service import BleakGATTService
from pytest import approx

from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvi_types import SensorHistoryData


def assert_history_data_equal(
    actual: dict | SensorHistoryData, expected: SensorHistoryData, float_tolerance: float = 0.01
) -> None:
    """Assert that history data dictionaries match, with tolerance for floating point values."""
    if expected.get("temperature") is not None:
        assert actual["temperature"] == approx(expected["temperature"], abs=float_tolerance)
    else:
        assert actual["temperature"] == expected.get("temperature")

    if expected.get("humidity") is not None:
        assert actual["humidity"] == approx(expected["humidity"], abs=float_tolerance)
    else:
        assert actual["humidity"] == expected.get("humidity")

    if expected.get("pressure") is not None:
        assert actual["pressure"] == approx(expected["pressure"], abs=1.0)
    else:
        assert actual["pressure"] == expected.get("pressure")

    assert actual["timestamp"] == expected["timestamp"]


HistoryTestCase = tuple[
    list[bytearray],  # notification_data: list of data packets (heartbeat, history data, etc.)
    list[SensorHistoryData],  # expected: list of expected decoded history data entries
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case",
    [
        # Test case: Temperature, humidity, and pressure history data with heartbeat
        # History data format: 0x3A [packet_type] [header] [4-byte timestamp] [2-byte reserved] [2-byte value]
        # Packet types: 0x30 = temperature, 0x31 = humidity, 0x32 = pressure
        # Temperature: 24.30°C = 2430 in 0.01°C units = 0x097E
        # Humidity: 53.49% = 5349 in 0.01% units = 0x14E5
        # Pressure: 1000 hPa (stored as raw value, not 0.01 units) = 0x03E8
        (
            [
                bytearray([0x05, 0x01, 0x02, 0x03, 0x04]),  # Heartbeat (should be ignored)
                bytearray(  # Temperature packet (0x30)
                    [
                        0x3A,  # Command byte
                        0x30,  # Temperature packet type
                        0x11,  # Header
                        (1700000000 >> 24) & 0xFF,
                        (1700000000 >> 16) & 0xFF,
                        (1700000000 >> 8) & 0xFF,
                        1700000000 & 0xFF,
                        0x00,  # Reserved
                        0x00,  # Reserved
                        (2430 >> 8) & 0xFF,  # Temperature high byte (24.30°C)
                        2430 & 0xFF,  # Temperature low byte
                    ]
                ),
                bytearray([0x05, 0x01, 0x02, 0x03, 0x04]),  # Heartbeat between packets (should be ignored)
                bytearray(  # Humidity packet (0x31)
                    [
                        0x3A,  # Command byte
                        0x31,  # Humidity packet type
                        0x11,  # Header
                        (1700000001 >> 24) & 0xFF,  # Timestamp + 1 second
                        (1700000001 >> 16) & 0xFF,
                        (1700000001 >> 8) & 0xFF,
                        1700000001 & 0xFF,
                        0x00,  # Reserved
                        0x00,  # Reserved
                        (5349 >> 8) & 0xFF,  # Humidity high byte (53.49%)
                        5349 & 0xFF,  # Humidity low byte
                    ]
                ),
                bytearray(  # Pressure packet (0x32)
                    [
                        0x3A,  # Command byte
                        0x32,  # Pressure packet type
                        0x11,  # Header
                        (1700000002 >> 24) & 0xFF,  # Timestamp + 2 seconds
                        (1700000002 >> 16) & 0xFF,
                        (1700000002 >> 8) & 0xFF,
                        1700000002 & 0xFF,
                        0x00,  # Reserved
                        0x00,  # Reserved
                        (1000 >> 8) & 0xFF,  # Pressure high byte (1000 hPa)
                        1000 & 0xFF,  # Pressure low byte
                    ]
                ),
                # Second round of readings
                bytearray(  # Temperature packet (0x30)
                    [
                        0x3A,  # Command byte
                        0x30,  # Temperature packet type
                        0x11,  # Header
                        (1700000060 >> 24) & 0xFF,
                        (1700000060 >> 16) & 0xFF,
                        (1700000060 >> 8) & 0xFF,
                        1700000060 & 0xFF,
                        0x00,  # Reserved
                        0x00,  # Reserved
                        (2500 >> 8) & 0xFF,  # Temperature high byte (25.00°C)
                        2500 & 0xFF,  # Temperature low byte
                    ]
                ),
                bytearray(  # Humidity packet (0x31)
                    [
                        0x3A,  # Command byte
                        0x31,  # Humidity packet type
                        0x11,  # Header
                        (1700000061 >> 24) & 0xFF,
                        (1700000061 >> 16) & 0xFF,
                        (1700000061 >> 8) & 0xFF,
                        1700000061 & 0xFF,
                        0x00,  # Reserved
                        0x00,  # Reserved
                        (5000 >> 8) & 0xFF,  # Humidity high byte (50.00%)
                        5000 & 0xFF,  # Humidity low byte
                    ]
                ),
                bytearray(  # Pressure packet (0x32)
                    [
                        0x3A,  # Command byte
                        0x32,  # Pressure packet type
                        0x11,  # Header
                        (1700000062 >> 24) & 0xFF,
                        (1700000062 >> 16) & 0xFF,
                        (1700000062 >> 8) & 0xFF,
                        1700000062 & 0xFF,
                        0x00,  # Reserved
                        0x00,  # Reserved
                        (1013 >> 8) & 0xFF,  # Pressure high byte (1013 hPa)
                        1013 & 0xFF,  # Pressure low byte
                    ]
                ),
                bytearray([0x3A, 0x3A, 0x10] + [0xFF] * 8),  # End marker
            ],
            [
                SensorHistoryData(
                    temperature=24.30,
                    humidity=None,
                    pressure=None,
                    timestamp=1700000000,
                ),
                SensorHistoryData(
                    temperature=None,
                    humidity=53.49,
                    pressure=None,
                    timestamp=1700000001,
                ),
                SensorHistoryData(
                    temperature=None,
                    humidity=None,
                    pressure=1000.0,
                    timestamp=1700000002,
                ),
                SensorHistoryData(
                    temperature=25.00,
                    humidity=None,
                    pressure=None,
                    timestamp=1700000060,
                ),
                SensorHistoryData(
                    temperature=None,
                    humidity=50.00,
                    pressure=None,
                    timestamp=1700000061,
                ),
                SensorHistoryData(
                    temperature=None,
                    humidity=None,
                    pressure=1013.0,
                    timestamp=1700000062,
                ),
            ],
        ),
    ],
)
@patch("ruuvitag_sensor.ruuvi.ble", new_callable=lambda: BleCommunicationBleak())
@patch("ruuvitag_sensor.adapters.bleak_ble.BleakClient")
async def test_get_history_async(mock_bleak_client, _mock_ble, test_case: HistoryTestCase):
    notification_data, expected_history = test_case
    mac = "AA:BB:CC:DD:EE:FF"

    # Create mock GATT service and characteristics
    mock_tx_char = AsyncMock(spec=BleakGATTCharacteristic)
    mock_rx_char = AsyncMock(spec=BleakGATTCharacteristic)
    mock_service = AsyncMock(spec=BleakGATTService)
    mock_service.uuid = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"  # NUS service UUID

    def get_characteristic_side_effect(uuid: str):
        # TX characteristic UUID ends with 003, RX ends with 002
        return mock_tx_char if "003" in uuid else mock_rx_char

    mock_service.get_characteristic = AsyncMock(side_effect=get_characteristic_side_effect)

    # Track notification handler
    notification_handler = None

    async def capture_notification_handler(_char, handler):
        nonlocal notification_handler
        notification_handler = handler

    # Create mock client
    mock_client = AsyncMock(spec=BleakClient)
    mock_client.services = [mock_service]
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.start_notify = AsyncMock(side_effect=capture_notification_handler)
    mock_client.write_gatt_char = AsyncMock()

    async def simulate_notifications():
        await asyncio.sleep(0.2)  # Wait for setup
        # Ensure notification handler was captured
        if notification_handler is None:
            raise RuntimeError("Notification handler was not captured")
        # Simulate receiving all notification data packets
        for data_packet in notification_data:
            notification_handler(mock_tx_char, data_packet)
            await asyncio.sleep(0.05)

    # Configure mock BleakClient to return our mock client
    mock_bleak_client.return_value = mock_client

    # Start notification simulation
    notification_task = asyncio.create_task(simulate_notifications())

    # Get history data
    history_items = [item async for item in RuuviTagSensor.get_history_async(mac)]

    # Wait for notification simulation to complete
    await notification_task

    assert len(history_items) == len(expected_history)
    for actual_item, expected_item in zip(history_items, expected_history, strict=True):
        assert_history_data_equal(actual_item, expected_item)

    mock_client.connect.assert_called_once()
    mock_client.start_notify.assert_called_once()
    mock_client.write_gatt_char.assert_called_once()
    mock_client.disconnect.assert_called_once()
