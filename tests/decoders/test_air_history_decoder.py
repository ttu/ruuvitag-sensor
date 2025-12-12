from ruuvitag_sensor.decoder import AirHistoryDecoder


class TestAirHistoryDecoder:
    def test_decode_single_record_packet(self):
        """Test decoding a packet with a single record."""
        decoder = AirHistoryDecoder()

        # Create a test record based on documentation format
        # Packet header: 0x3B 3B 20 01 26 (1 record, 38 bytes each)
        # Record: timestamp (4 bytes) + E1 data (34 bytes)
        # Example from docs: timestamp 1733760000, temperature 24.3°C, etc.
        timestamp = 1733760000  # 2024-12-09 16:00:00 UTC
        # Temperature: 24.3°C = 24.3 * 200 = 4860 = 0x12FC (int16_t BE)
        # Humidity: 53.49% = 53.49 * 400 = 21396 = 0x5394 (uint16_t BE)
        # Pressure: 100000 Pa = (100000 - 50000) = 50000 = 0xC350 (uint16_t BE)
        # PM2.5: 10.0 µg/m³ = 10.0 * 10 = 100 = 0x0064 (uint16_t BE)
        # CO₂: 450 ppm = 0x01C2 (uint16_t BE)
        # VOC: 50 (byte 21 = 0x32, flags bit 6 = 0)
        # NOx: 25 (byte 22 = 0x19, flags bit 7 = 0)
        # Sequence: 12345 = 0x003039 (uint24_t BE)
        # Flags: 0x00 (no extended bits)

        record_data = bytearray(
            [
                # Timestamp (4 bytes, big-endian)
                (timestamp >> 24) & 0xFF,
                (timestamp >> 16) & 0xFF,
                (timestamp >> 8) & 0xFF,
                timestamp & 0xFF,
                # Data format
                0xE1,
                # Temperature (int16_t BE, 4860 = 0x12FC)
                0x12,
                0xFC,
                # Humidity (uint16_t BE, 21396 = 0x5394)
                0x53,
                0x94,
                # Pressure (uint16_t BE, 50000 = 0xC350)
                0xC3,
                0x50,
                # PM1.0 (uint16_t BE, 50 = 0x0032)
                0x00,
                0x32,
                # PM2.5 (uint16_t BE, 100 = 0x0064)
                0x00,
                0x64,
                # PM4.0 (uint16_t BE, 80 = 0x0050)
                0x00,
                0x50,
                # PM10.0 (uint16_t BE, 120 = 0x0078)
                0x00,
                0x78,
                # CO₂ (uint16_t BE, 450 = 0x01C2)
                0x01,
                0xC2,
                # VOC (uint8_t, 50 = 0x32)
                0x32,
                # NOx (uint8_t, 25 = 0x19)
                0x19,
                # Reserved (bytes 23-28)
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                # Sequence counter (uint24_t BE, 12345 = 0x003039)
                0x00,
                0x30,
                0x39,
                # Flags (byte 32)
                0x00,
                # Reserved (bytes 33-37)
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        # Create packet with header + record
        packet = bytearray([0x3B, 0x3B, 0x20, 0x01, 0x26]) + record_data

        records = decoder.decode_data(packet)
        assert len(records) == 1

        record = records[0]
        assert record["timestamp"] == timestamp
        assert record["temperature"] == 24.3
        assert record["humidity"] == 53.49
        assert record["pressure"] == 1000.0  # (50000 + 50000) / 100
        assert record["pm_1"] == 5.0  # 50 / 10
        assert record["pm_2_5"] == 10.0  # 100 / 10
        assert record["pm_4"] == 8.0  # 80 / 10
        assert record["pm_10"] == 12.0  # 120 / 10
        assert record["co2"] == 450
        assert record["voc"] == 50
        assert record["nox"] == 25
        assert record["measurement_sequence_number"] == 12345

    def test_decode_multiple_records_packet(self):
        """Test decoding a packet with multiple records."""
        decoder = AirHistoryDecoder()

        # Create two records
        timestamp1 = 1733760000
        timestamp2 = 1733760300  # 5 minutes later

        record1 = bytearray(
            [
                (timestamp1 >> 24) & 0xFF,
                (timestamp1 >> 16) & 0xFF,
                (timestamp1 >> 8) & 0xFF,
                timestamp1 & 0xFF,
                0xE1,
                0x12,
                0xFC,
                0x53,
                0x94,
                0xC3,
                0x50,
                0x00,
                0x32,
                0x00,
                0x64,
                0x00,
                0x50,
                0x00,
                0x78,
                0x01,
                0xC2,
                0x32,
                0x19,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x30,
                0x39,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        record2 = bytearray(
            [
                (timestamp2 >> 24) & 0xFF,
                (timestamp2 >> 16) & 0xFF,
                (timestamp2 >> 8) & 0xFF,
                timestamp2 & 0xFF,
                0xE1,
                0x13,
                0x88,
                0x54,
                0x60,
                0xC3,
                0x51,
                0x00,
                0x33,
                0x00,
                0x65,
                0x00,
                0x51,
                0x00,
                0x79,
                0x01,
                0xC3,
                0x33,
                0x1A,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x30,
                0x3A,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        # Packet with 2 records
        packet = bytearray([0x3B, 0x3B, 0x20, 0x02, 0x26]) + record1 + record2

        records = decoder.decode_data(packet)
        assert len(records) == 2
        assert records[0]["timestamp"] == timestamp1
        assert records[1]["timestamp"] == timestamp2

    def test_decode_end_marker(self):
        """Test decoding end marker packet."""
        decoder = AirHistoryDecoder()

        # End marker: 0x3B 3B 20 00 26
        end_marker = bytearray([0x3B, 0x3B, 0x20, 0x00, 0x26])

        records = decoder.decode_data(end_marker)
        assert len(records) == 0

    def test_decode_invalid_data_format(self):
        """Test decoding record with invalid data format."""
        decoder = AirHistoryDecoder()

        timestamp = 1733760000
        record_data = bytearray(
            [
                (timestamp >> 24) & 0xFF,
                (timestamp >> 16) & 0xFF,
                (timestamp >> 8) & 0xFF,
                timestamp & 0xFF,
                0xE2,  # Wrong data format (should be 0xE1)
                0x12,
                0xFC,
                0x53,
                0x94,
                0xC3,
                0x50,
                0x00,
                0x32,
                0x00,
                0x64,
                0x00,
                0x50,
                0x00,
                0x78,
                0x01,
                0xC2,
                0x32,
                0x19,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x30,
                0x39,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        packet = bytearray([0x3B, 0x3B, 0x20, 0x01, 0x26]) + record_data

        records = decoder.decode_data(packet)
        assert len(records) == 0  # Invalid record should be skipped

    def test_decode_invalid_temperature(self):
        """Test decoding record with invalid temperature value."""
        decoder = AirHistoryDecoder()

        timestamp = 1733760000
        record_data = bytearray(
            [
                (timestamp >> 24) & 0xFF,
                (timestamp >> 16) & 0xFF,
                (timestamp >> 8) & 0xFF,
                timestamp & 0xFF,
                0xE1,
                0x80,
                0x00,  # Invalid temperature (0x8000)
                0x53,
                0x94,
                0xC3,
                0x50,
                0x00,
                0x32,
                0x00,
                0x64,
                0x00,
                0x50,
                0x00,
                0x78,
                0x01,
                0xC2,
                0x32,
                0x19,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x30,
                0x39,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        packet = bytearray([0x3B, 0x3B, 0x20, 0x01, 0x26]) + record_data

        records = decoder.decode_data(packet)
        assert len(records) == 1
        assert records[0]["temperature"] is None

    def test_decode_invalid_humidity(self):
        """Test decoding record with invalid humidity value."""
        decoder = AirHistoryDecoder()

        timestamp = 1733760000
        record_data = bytearray(
            [
                (timestamp >> 24) & 0xFF,
                (timestamp >> 16) & 0xFF,
                (timestamp >> 8) & 0xFF,
                timestamp & 0xFF,
                0xE1,
                0x12,
                0xFC,
                0xFF,
                0xFF,  # Invalid humidity (0xFFFF)
                0xC3,
                0x50,
                0x00,
                0x32,
                0x00,
                0x64,
                0x00,
                0x50,
                0x00,
                0x78,
                0x01,
                0xC2,
                0x32,
                0x19,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x30,
                0x39,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        packet = bytearray([0x3B, 0x3B, 0x20, 0x01, 0x26]) + record_data

        records = decoder.decode_data(packet)
        assert len(records) == 1
        assert records[0]["humidity"] is None

    def test_decode_voc_nox_with_flags(self):
        """Test decoding VOC and NOx with 9-bit values using flags."""
        decoder = AirHistoryDecoder()

        timestamp = 1733760000
        # VOC: byte 21 = 0xF4 (244), flags bit 6 = 1 -> 244 | (1 << 8) = 244 | 256 = 500
        # NOx: byte 22 = 0xFA (250), flags bit 7 = 1 -> 250 | (1 << 8) = 250 | 256 = 506
        record_data = bytearray(
            [
                (timestamp >> 24) & 0xFF,
                (timestamp >> 16) & 0xFF,
                (timestamp >> 8) & 0xFF,
                timestamp & 0xFF,
                0xE1,
                0x12,
                0xFC,
                0x53,
                0x94,
                0xC3,
                0x50,
                0x00,
                0x32,
                0x00,
                0x64,
                0x00,
                0x50,
                0x00,
                0x78,
                0x01,
                0xC2,
                0xF4,  # VOC byte (bits [7:0] = 244)
                0xFA,  # NOx byte (bits [7:0] = 250)
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x30,
                0x39,
                0xC0,  # Flags: bit 6 = 1 (VOC bit 9), bit 7 = 1 (NOx bit 9)
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        packet = bytearray([0x3B, 0x3B, 0x20, 0x01, 0x26]) + record_data

        records = decoder.decode_data(packet)
        assert len(records) == 1
        # VOC: 0xF4 | (1 << 8) = 244 | 256 = 500
        assert records[0]["voc"] == 500
        # NOx: 0xFA | (1 << 8) = 250 | 256 = 506
        assert records[0]["nox"] == 506

    def test_decode_invalid_voc_nox(self):
        """Test decoding record with invalid VOC/NOx values."""
        decoder = AirHistoryDecoder()

        timestamp = 1733760000
        # VOC: 0xFF (255) with bit 9 = 1 -> 511 (invalid)
        # NOx: 0xFF (255) with bit 9 = 1 -> 511 (invalid)
        record_data = bytearray(
            [
                (timestamp >> 24) & 0xFF,
                (timestamp >> 16) & 0xFF,
                (timestamp >> 8) & 0xFF,
                timestamp & 0xFF,
                0xE1,
                0x12,
                0xFC,
                0x53,
                0x94,
                0xC3,
                0x50,
                0x00,
                0x32,
                0x00,
                0x64,
                0x00,
                0x50,
                0x00,
                0x78,
                0x01,
                0xC2,
                0xFF,  # VOC byte
                0xFF,  # NOx byte
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x30,
                0x39,
                0xC0,  # Flags: bit 6 = 1, bit 7 = 1
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        packet = bytearray([0x3B, 0x3B, 0x20, 0x01, 0x26]) + record_data

        records = decoder.decode_data(packet)
        assert len(records) == 1
        assert records[0]["voc"] is None  # 511 is invalid
        assert records[0]["nox"] is None  # 511 is invalid

    def test_decode_invalid_sequence(self):
        """Test decoding record with invalid sequence counter."""
        decoder = AirHistoryDecoder()

        timestamp = 1733760000
        record_data = bytearray(
            [
                (timestamp >> 24) & 0xFF,
                (timestamp >> 16) & 0xFF,
                (timestamp >> 8) & 0xFF,
                timestamp & 0xFF,
                0xE1,
                0x12,
                0xFC,
                0x53,
                0x94,
                0xC3,
                0x50,
                0x00,
                0x32,
                0x00,
                0x64,
                0x00,
                0x50,
                0x00,
                0x78,
                0x01,
                0xC2,
                0x32,
                0x19,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0xFF,
                0xFF,
                0xFF,  # Invalid sequence (0xFFFFFF)
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )

        packet = bytearray([0x3B, 0x3B, 0x20, 0x01, 0x26]) + record_data

        records = decoder.decode_data(packet)
        assert len(records) == 1
        assert records[0]["measurement_sequence_number"] is None

    def test_decode_invalid_packet_header(self):
        """Test decoding packet with invalid header."""
        decoder = AirHistoryDecoder()

        # Invalid header (wrong destination/source/operation)
        invalid_packet = bytearray([0x3A, 0x3A, 0x20, 0x01, 0x26])

        records = decoder.decode_data(invalid_packet)
        assert len(records) == 0

    def test_decode_short_packet(self):
        """Test decoding packet that's too short."""
        decoder = AirHistoryDecoder()

        short_packet = bytearray([0x3B, 0x3B, 0x20])

        records = decoder.decode_data(short_packet)
        assert len(records) == 0

    def test_decode_short_record(self):
        """Test decoding packet with incomplete record."""
        decoder = AirHistoryDecoder()

        # Packet claims 1 record but data is incomplete
        incomplete_packet = bytearray([0x3B, 0x3B, 0x20, 0x01, 0x26]) + bytearray([0x00] * 20)

        records = decoder.decode_data(incomplete_packet)
        assert len(records) == 0  # Incomplete record should be skipped
