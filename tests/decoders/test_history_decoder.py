from datetime import datetime, timezone

from ruuvitag_sensor.decoder import HistoryDecoder


class TestHistoryDecoder:
    def test_history_decode_docs_temperature(self):
        # Data from: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        # 0x3A 30 10 5D57FEAD 000000098D
        sample_clean = ["3a", "30", "10", "5D", "57", "FE", "AD", "00", "00", "09", "8D"]
        sample_bytes = bytearray.fromhex("".join(sample_clean))
        decoder = HistoryDecoder()
        data = decoder.decode_data(sample_bytes)
        # 2019-08-13 13:18 24.45 C"
        assert data["temperature"] == 24.45
        # TODO: Check datetime if it is correct in docs
        assert (
            data["timestamp"] == datetime(2019, 8, 17, 13, 18, 37, tzinfo=timezone.utc).timestamp()
        )  # datetime(2019, 8, 13, 13, 18, 37)

    def test_history_decode_docs_humidity(self):
        # Data from: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        # 0x3A 31 10 5D57FEAD 000000098D
        sample_clean = ["3a", "31", "10", "5D", "57", "FE", "AD", "00", "00", "09", "8D"]
        sample_bytes = bytearray.fromhex("".join(sample_clean))
        decoder = HistoryDecoder()
        data = decoder.decode_data(sample_bytes)
        # 2019-08-13 13:18 24.45 RH-%
        assert data["humidity"] == 24.45
        # TODO: Check datetime if it is correct in docs
        assert (
            data["timestamp"] == datetime(2019, 8, 17, 13, 18, 37, tzinfo=timezone.utc).timestamp()
        )  # datetime(2019, 8, 13, 13, 18, 37)

    def test_history_decode_docs_pressure(self):
        # Data from: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        # 0x3A 32 10 5D57FEAD 000000098D
        sample_clean = ["3a", "32", "10", "5D", "57", "FE", "AD", "00", "00", "09", "8D"]
        sample_bytes = bytearray.fromhex("".join(sample_clean))
        decoder = HistoryDecoder()
        data = decoder.decode_data(sample_bytes)
        # 2019-08-13 13:18 2445 Pa
        assert data["pressure"] == 2445
        # TODO: Check datetime if it is correct in docs
        assert (
            data["timestamp"] == datetime(2019, 8, 17, 13, 18, 37, tzinfo=timezone.utc).timestamp()
        )  # datetime(2019, 8, 13, 13, 18, 37)

    def test_history_decode_real_samples(self):
        decoder = HistoryDecoder()

        # Test temperature data
        data = bytearray(b':0\x10g\x9d\xb5"\x00\x00\x08\xe3')
        result = decoder.decode_data(data)
        assert result is not None
        assert result["temperature"] == 22.75
        assert result["humidity"] is None
        assert result["pressure"] is None
        assert result["timestamp"] == datetime(2025, 2, 1, 5, 46, 10, tzinfo=timezone.utc).timestamp()

        # Test humidity data
        data = bytearray(b':1\x10g\x9d\xb5"\x00\x00\x10\x90')
        result = decoder.decode_data(data)
        assert result is not None
        assert result["humidity"] == 42.4
        assert result["temperature"] is None
        assert result["pressure"] is None
        assert result["timestamp"] == datetime(2025, 2, 1, 5, 46, 10, tzinfo=timezone.utc).timestamp()

        # Test pressure data
        data = bytearray(b':2\x10g\x9d\xb5"\x00\x01\x8b@')
        result = decoder.decode_data(data)
        assert result is not None
        assert result["pressure"] == 35648
        assert result["temperature"] is None
        assert result["humidity"] is None
        assert result["timestamp"] == datetime(2025, 2, 1, 5, 46, 10, tzinfo=timezone.utc).timestamp()

    def test_history_end_marker(self):
        decoder = HistoryDecoder()
        data = bytearray(b"::\x10\xff\xff\xff\xff\xff\xff\xff\xff")
        result = decoder.decode_data(data)
        assert result is None

    def test_history_decode_is_error(self):
        decoder = HistoryDecoder()

        error_cases = [
            bytearray(b";\x10g\x9b\xb2\xaf\x00\x00\x08\xac"),  # 0x3B
            bytearray(b"9\x10g\x9b\xb2\xaf\x00\x00\x08\xac"),  # 0x39
            bytearray(b"?\x10g\x9b\xb2\xaf\x00\x00\x08\xac"),  # 0x3F
            bytearray(b""),  # Empty data
            bytearray(b":"),  # Too short
            bytearray(b":\x10"),  # Incomplete data
        ]
        for error_data in error_cases:
            assert decoder.decode_data(error_data) is None, f"Should be error for data: {error_data!r}"

    def test_history_decode_detects_ruuvi_air_data(self):
        """Test that HistoryDecoder detects and logs helpful error for Ruuvi Air data."""
        decoder = HistoryDecoder()

        # Simulate Ruuvi Air packet data (various formats that might be received)
        # This is what would be received from a Ruuvi Air device when using wrong device_type
        air_data_cases = [
            # Multi-record packet header starting with 0x3B
            bytearray(b"\x3b\x3b\x20\x01\x26" + b"\x00" * 38),
            # Single record with 0xE1 format at byte 4 (inside packet)
            bytearray(b"\x00\x00\x00\x00\xe1" + b"\x00" * 33),
            # Raw 38-byte record starting with 0xE1
            bytearray(
                b"\xe1\x118/l\xcbD\x00\x02\x00\x04\x00\x06\x00\x07\x02Y$\x00\xff\xff\xff\xff\xff\xff0G\xfe\xb8\xff\xff\xff\xff\xff"
            ),
            # Raw 34-byte record starting with 0xE1 (actual case from real device)
            bytearray(
                b"\xe1\x113.\x90\xcc\x10\x00\x05\x00\n\x00\x0f\x00\x11\x02/*\x00\xff\xff\xff\xff\xff\xff0n\x86\xb8"
            ),
        ]

        # Process all test cases and verify they all return None
        for air_data in air_data_cases:
            result = decoder.decode_data(air_data)
            assert result is None
