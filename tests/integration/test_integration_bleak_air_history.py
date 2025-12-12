import asyncio
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.service import BleakGATTService
from pytest import approx

from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvi_types import SensorAirHistoryData


def assert_air_history_data_equal(  # noqa: PLR0912 - Test utility function, branches are clear
    actual: dict | SensorAirHistoryData, expected: SensorAirHistoryData, float_tolerance: float = 0.01
) -> None:
    """Assert that air history data dictionaries match, with tolerance for floating point values."""
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

    if expected.get("pm_1") is not None:
        assert actual["pm_1"] == approx(expected["pm_1"], abs=float_tolerance)
    else:
        assert actual["pm_1"] == expected.get("pm_1")

    if expected.get("pm_2_5") is not None:
        assert actual["pm_2_5"] == approx(expected["pm_2_5"], abs=float_tolerance)
    else:
        assert actual["pm_2_5"] == expected.get("pm_2_5")

    if expected.get("co2") is not None:
        assert actual["co2"] == expected["co2"]
    else:
        assert actual["co2"] == expected.get("co2")

    if expected.get("voc") is not None:
        assert actual["voc"] == expected["voc"]
    else:
        assert actual["voc"] == expected.get("voc")

    if expected.get("nox") is not None:
        assert actual["nox"] == expected["nox"]
    else:
        assert actual["nox"] == expected.get("nox")

    assert actual["timestamp"] == expected["timestamp"]


AirHistoryTestCase = tuple[
    list[bytearray],  # notification_data: list of data packets (heartbeat, history data, etc.)
    list[SensorAirHistoryData],  # expected: list of expected decoded history data entries
]


def create_air_history_record(  # noqa: PLR0912, PLR0913, PLR0915, C901 - Test helper needs many params/branches to construct test data
    timestamp: int,
    temperature: float | None = None,
    humidity: float | None = None,
    pressure: float | None = None,
    pm1: float | None = None,
    pm25: float | None = None,
    pm4: float | None = None,
    pm10: float | None = None,
    co2: int | None = None,
    voc: int | None = None,
    nox: int | None = None,
    sequence: int | None = None,
) -> bytearray:
    """Create a 38-byte Ruuvi Air history record."""
    record = bytearray(38)

    # Timestamp (bytes 0-3, big-endian)
    record[0] = (timestamp >> 24) & 0xFF
    record[1] = (timestamp >> 16) & 0xFF
    record[2] = (timestamp >> 8) & 0xFF
    record[3] = timestamp & 0xFF

    # Data format (byte 4)
    record[4] = 0xE1

    # Temperature (bytes 5-6, int16_t BE)
    if temperature is not None:
        temp_raw = int(temperature * 200)
        record[5] = (temp_raw >> 8) & 0xFF
        record[6] = temp_raw & 0xFF
    else:
        record[5] = 0x80
        record[6] = 0x00  # Invalid marker

    # Humidity (bytes 7-8, uint16_t BE)
    if humidity is not None:
        hum_raw = int(humidity * 400)
        record[7] = (hum_raw >> 8) & 0xFF
        record[8] = hum_raw & 0xFF
    else:
        record[7] = 0xFF
        record[8] = 0xFF  # Invalid marker

    # Pressure (bytes 9-10, uint16_t BE)
    if pressure is not None:
        press_raw = int((pressure * 100) - 50000)
        record[9] = (press_raw >> 8) & 0xFF
        record[10] = press_raw & 0xFF
    else:
        record[9] = 0xFF
        record[10] = 0xFF  # Invalid marker

    # PM values (bytes 11-18, uint16_t BE, x 10)
    if pm1 is not None:
        pm1_raw = int(pm1 * 10)
        record[11] = (pm1_raw >> 8) & 0xFF
        record[12] = pm1_raw & 0xFF
    else:
        record[11] = 0xFF
        record[12] = 0xFF

    if pm25 is not None:
        pm25_raw = int(pm25 * 10)
        record[13] = (pm25_raw >> 8) & 0xFF
        record[14] = pm25_raw & 0xFF
    else:
        record[13] = 0xFF
        record[14] = 0xFF

    if pm4 is not None:
        pm4_raw = int(pm4 * 10)
        record[15] = (pm4_raw >> 8) & 0xFF
        record[16] = pm4_raw & 0xFF
    else:
        record[15] = 0xFF
        record[16] = 0xFF

    if pm10 is not None:
        pm10_raw = int(pm10 * 10)
        record[17] = (pm10_raw >> 8) & 0xFF
        record[18] = pm10_raw & 0xFF
    else:
        record[17] = 0xFF
        record[18] = 0xFF

    # CO₂ (bytes 19-20, uint16_t BE)
    if co2 is not None:
        record[19] = (co2 >> 8) & 0xFF
        record[20] = co2 & 0xFF
    else:
        record[19] = 0xFF
        record[20] = 0xFF

    # VOC (byte 21) and NOx (byte 22)
    flags = 0
    if voc is not None:
        if voc >= 512:  # Invalid
            record[21] = 0xFF
            flags |= 0x40  # Set bit 6
        else:
            record[21] = voc & 0xFF
            flags |= ((voc >> 8) & 0x01) << 6
    else:
        record[21] = 0xFF
        flags |= 0x40

    if nox is not None:
        if nox >= 512:  # Invalid
            record[22] = 0xFF
            flags |= 0x80  # Set bit 7
        else:
            record[22] = nox & 0xFF
            flags |= ((nox >> 8) & 0x01) << 7
    else:
        record[22] = 0xFF
        flags |= 0x80

    # Reserved (bytes 23-28)
    for i in range(23, 29):
        record[i] = 0x00

    # Sequence counter (bytes 29-31, uint24_t BE)
    if sequence is not None:
        record[29] = (sequence >> 16) & 0xFF
        record[30] = (sequence >> 8) & 0xFF
        record[31] = sequence & 0xFF
    else:
        record[29] = 0xFF
        record[30] = 0xFF
        record[31] = 0xFF

    # Flags (byte 32)
    record[32] = flags

    # Reserved (bytes 33-37)
    for i in range(33, 38):
        record[i] = 0x00

    return record


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_case",
    [
        # Test case: Multiple packets, each with multiple readings, heartbeats between packets
        (
            [
                # First packet: 2 records
                bytearray([0x3B, 0x3B, 0x20, 0x02, 0x26])  # Packet header: 2 records, 38 bytes each
                + create_air_history_record(
                    timestamp=1733760000,
                    temperature=24.3,
                    humidity=53.49,
                    pressure=1000.0,
                    pm1=5.0,
                    pm25=10.0,
                    pm4=8.0,
                    pm10=12.0,
                    co2=450,
                    voc=50,
                    nox=25,
                    sequence=12345,
                )
                + create_air_history_record(
                    timestamp=1733760300,  # 5 minutes later
                    temperature=24.5,
                    humidity=53.6,
                    pressure=1000.1,
                    pm1=5.1,
                    pm25=10.1,
                    pm4=8.1,
                    pm10=12.1,
                    co2=451,
                    voc=51,
                    nox=26,
                    sequence=12346,
                ),
                bytearray([0x05, 0x01, 0x02, 0x03, 0x04]),  # Heartbeat between packets (should be ignored)
                # Second packet: 2 records
                bytearray([0x3B, 0x3B, 0x20, 0x02, 0x26])  # Packet header: 2 records, 38 bytes each
                + create_air_history_record(
                    timestamp=1733760600,  # 10 minutes later
                    temperature=24.7,
                    humidity=53.8,
                    pressure=1000.2,
                    pm1=5.2,
                    pm25=10.2,
                    pm4=8.2,
                    pm10=12.2,
                    co2=452,
                    voc=52,
                    nox=27,
                    sequence=12347,
                )
                + create_air_history_record(
                    timestamp=1733760900,  # 15 minutes later
                    temperature=24.9,
                    humidity=54.0,
                    pressure=1000.3,
                    pm1=5.3,
                    pm25=10.3,
                    pm4=8.3,
                    pm10=12.3,
                    co2=453,
                    voc=53,
                    nox=28,
                    sequence=12348,
                ),
                bytearray([0x05, 0x01, 0x02, 0x03, 0x04]),  # Heartbeat between packets (should be ignored)
                # Third packet: 2 records
                bytearray([0x3B, 0x3B, 0x20, 0x02, 0x26])  # Packet header: 2 records, 38 bytes each
                + create_air_history_record(
                    timestamp=1733761200,  # 20 minutes later
                    temperature=25.1,
                    humidity=54.2,
                    pressure=1000.4,
                    pm1=5.4,
                    pm25=10.4,
                    pm4=8.4,
                    pm10=12.4,
                    co2=454,
                    voc=54,
                    nox=29,
                    sequence=12349,
                )
                + create_air_history_record(
                    timestamp=1733761500,  # 25 minutes later
                    temperature=25.3,
                    humidity=54.4,
                    pressure=1000.5,
                    pm1=5.5,
                    pm25=10.5,
                    pm4=8.5,
                    pm10=12.5,
                    co2=455,
                    voc=55,
                    nox=30,
                    sequence=12350,
                ),
                bytearray([0x3B, 0x3B, 0x20, 0x00, 0x26]),  # End marker
            ],
            [
                SensorAirHistoryData(
                    timestamp=1733760000,
                    temperature=24.3,
                    humidity=53.49,
                    pressure=1000.0,
                    pm_1=5.0,
                    pm_2_5=10.0,
                    pm_4=8.0,
                    pm_10=12.0,
                    co2=450,
                    voc=50,
                    nox=25,
                    measurement_sequence_number=12345,
                ),
                SensorAirHistoryData(
                    timestamp=1733760300,
                    temperature=24.5,
                    humidity=53.6,
                    pressure=1000.1,
                    pm_1=5.1,
                    pm_2_5=10.1,
                    pm_4=8.1,
                    pm_10=12.1,
                    co2=451,
                    voc=51,
                    nox=26,
                    measurement_sequence_number=12346,
                ),
                SensorAirHistoryData(
                    timestamp=1733760600,
                    temperature=24.7,
                    humidity=53.8,
                    pressure=1000.2,
                    pm_1=5.2,
                    pm_2_5=10.2,
                    pm_4=8.2,
                    pm_10=12.2,
                    co2=452,
                    voc=52,
                    nox=27,
                    measurement_sequence_number=12347,
                ),
                SensorAirHistoryData(
                    timestamp=1733760900,
                    temperature=24.9,
                    humidity=54.0,
                    pressure=1000.3,
                    pm_1=5.3,
                    pm_2_5=10.3,
                    pm_4=8.3,
                    pm_10=12.3,
                    co2=453,
                    voc=53,
                    nox=28,
                    measurement_sequence_number=12348,
                ),
                SensorAirHistoryData(
                    timestamp=1733761200,
                    temperature=25.1,
                    humidity=54.2,
                    pressure=1000.4,
                    pm_1=5.4,
                    pm_2_5=10.4,
                    pm_4=8.4,
                    pm_10=12.4,
                    co2=454,
                    voc=54,
                    nox=29,
                    measurement_sequence_number=12349,
                ),
                SensorAirHistoryData(
                    timestamp=1733761500,
                    temperature=25.3,
                    humidity=54.4,
                    pressure=1000.5,
                    pm_1=5.5,
                    pm_2_5=10.5,
                    pm_4=8.5,
                    pm_10=12.5,
                    co2=455,
                    voc=55,
                    nox=30,
                    measurement_sequence_number=12350,
                ),
            ],
        ),
        # Test case: Multiple records in one packet
        (
            [
                bytearray([0x3B, 0x3B, 0x20, 0x02, 0x26])  # Packet header: 2 records, 38 bytes each
                + create_air_history_record(
                    timestamp=1733760000,
                    temperature=24.3,
                    humidity=53.49,
                    pressure=1000.0,
                    pm1=5.0,
                    pm25=10.0,
                    pm4=8.0,
                    pm10=12.0,
                    co2=450,
                    voc=50,
                    nox=25,
                    sequence=12345,
                )
                + create_air_history_record(
                    timestamp=1733760300,  # 5 minutes later
                    temperature=24.5,
                    humidity=53.6,
                    pressure=1000.1,
                    pm1=5.1,
                    pm25=10.1,
                    pm4=8.1,
                    pm10=12.1,
                    co2=451,
                    voc=51,
                    nox=26,
                    sequence=12346,
                ),
                bytearray([0x3B, 0x3B, 0x20, 0x00, 0x26]),  # End marker
            ],
            [
                SensorAirHistoryData(
                    timestamp=1733760000,
                    temperature=24.3,
                    humidity=53.49,
                    pressure=1000.0,
                    pm_1=5.0,
                    pm_2_5=10.0,
                    pm_4=8.0,
                    pm_10=12.0,
                    co2=450,
                    voc=50,
                    nox=25,
                    measurement_sequence_number=12345,
                ),
                SensorAirHistoryData(
                    timestamp=1733760300,
                    temperature=24.5,
                    humidity=53.6,
                    pressure=1000.1,
                    pm_1=5.1,
                    pm_2_5=10.1,
                    pm_4=8.1,
                    pm_10=12.1,
                    co2=451,
                    voc=51,
                    nox=26,
                    measurement_sequence_number=12346,
                ),
            ],
        ),
    ],
)
@patch("ruuvitag_sensor.ruuvi.ble", new_callable=lambda: BleCommunicationBleak())
@patch("ruuvitag_sensor.adapters.bleak_ble.BleakClient")
async def test_get_air_history_async(mock_bleak_client, _mock_ble, test_case: AirHistoryTestCase):
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
    mock_client.set_mtu = AsyncMock()
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

    # Get history data (explicitly specify Ruuvi Air device type)
    history_items = [item async for item in RuuviTagSensor.get_history_async(mac, device_type="ruuvi_air")]

    # Wait for notification simulation to complete
    await notification_task

    # For Ruuvi Air, the device sends multiple records per packet, but the library yields records one-by-one.
    assert len(history_items) == len(expected_history)
    for actual_item, expected_item in zip(history_items, expected_history, strict=True):
        # Cast to SensorAirHistoryData since we know device_type="ruuvi_air" returns only Air history data
        assert_air_history_data_equal(cast(SensorAirHistoryData, actual_item), expected_item)

    mock_client.connect.assert_called_once()
    mock_client.set_mtu.assert_called_once_with(247)
    mock_client.start_notify.assert_called_once()
    mock_client.write_gatt_char.assert_called_once()
    mock_client.disconnect.assert_called_once()


@pytest.mark.asyncio
@patch("ruuvitag_sensor.ruuvi.ble", new_callable=lambda: BleCommunicationBleak())
@patch("ruuvitag_sensor.adapters.bleak_ble.BleakClient")
async def test_download_air_history(mock_bleak_client, _mock_ble):
    """Test download_air_history method."""
    mac = "AA:BB:CC:DD:EE:FF"

    # Create test data - multiple packets, each with multiple readings, heartbeats between packets
    record1 = create_air_history_record(
        timestamp=1733760000,
        temperature=24.3,
        humidity=53.49,
        pressure=1000.0,
        pm1=5.0,
        pm25=10.0,
        co2=450,
        voc=50,
        nox=25,
        sequence=12345,
    )
    record2 = create_air_history_record(
        timestamp=1733760300,
        temperature=24.5,
        humidity=53.6,
        pressure=1000.1,
        pm1=5.1,
        pm25=10.1,
        co2=451,
        voc=51,
        nox=26,
        sequence=12346,
    )
    record3 = create_air_history_record(
        timestamp=1733760600,
        temperature=24.7,
        humidity=53.8,
        pressure=1000.2,
        pm1=5.2,
        pm25=10.2,
        co2=452,
        voc=52,
        nox=27,
        sequence=12347,
    )
    record4 = create_air_history_record(
        timestamp=1733760900,
        temperature=24.9,
        humidity=54.0,
        pressure=1000.3,
        pm1=5.3,
        pm25=10.3,
        co2=453,
        voc=53,
        nox=28,
        sequence=12348,
    )

    notification_data = [
        # First packet: 2 records
        bytearray([0x3B, 0x3B, 0x20, 0x02, 0x26]) + record1 + record2,
        bytearray([0x05, 0x01, 0x02, 0x03, 0x04]),  # Heartbeat between packets (should be ignored)
        # Second packet: 2 records
        bytearray([0x3B, 0x3B, 0x20, 0x02, 0x26]) + record3 + record4,
        bytearray([0x3B, 0x3B, 0x20, 0x00, 0x26]),  # End marker
    ]

    # Create mock GATT service and characteristics
    mock_tx_char = AsyncMock(spec=BleakGATTCharacteristic)
    mock_rx_char = AsyncMock(spec=BleakGATTCharacteristic)
    mock_service = AsyncMock(spec=BleakGATTService)
    mock_service.uuid = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"

    def get_characteristic_side_effect(uuid: str):
        return mock_tx_char if "003" in uuid else mock_rx_char

    mock_service.get_characteristic = AsyncMock(side_effect=get_characteristic_side_effect)

    notification_handler = None

    async def capture_notification_handler(_char, handler):
        nonlocal notification_handler
        notification_handler = handler

    mock_client = AsyncMock(spec=BleakClient)
    mock_client.services = [mock_service]
    mock_client.connect = AsyncMock()
    mock_client.disconnect = AsyncMock()
    mock_client.set_mtu = AsyncMock()
    mock_client.start_notify = AsyncMock(side_effect=capture_notification_handler)
    mock_client.write_gatt_char = AsyncMock()

    async def simulate_notifications():
        await asyncio.sleep(0.2)
        if notification_handler is None:
            raise RuntimeError("Notification handler was not captured")
        for data_packet in notification_data:
            notification_handler(mock_tx_char, data_packet)
            await asyncio.sleep(0.05)

    mock_bleak_client.return_value = mock_client
    notification_task = asyncio.create_task(simulate_notifications())

    # Download history data (explicitly specify Ruuvi Air device type)
    history_items = await RuuviTagSensor.download_history(mac, timeout=5, device_type="ruuvi_air")

    await notification_task

    assert len(history_items) == 4
    assert history_items[0]["timestamp"] == 1733760000
    assert history_items[1]["timestamp"] == 1733760300
    assert history_items[2]["timestamp"] == 1733760600
    assert history_items[3]["timestamp"] == 1733760900

    mock_client.connect.assert_called_once()
    mock_client.disconnect.assert_called_once()
