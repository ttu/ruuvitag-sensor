from ruuvitag_sensor.adapters.bleak_ble import BleCommunicationBleak, HistoryNotificationAction


class TestHistoryNotificationProcessing:
    def test_ignore_heartbeat_data(self):
        """Test that heartbeat data (starting with 0x05) is ignored."""
        adapter = BleCommunicationBleak()
        # Heartbeat data starts with 0x05
        heartbeat_data = bytearray([0x05, 0x01, 0x02, 0x03, 0x04])

        action, data = adapter._process_history_notification(heartbeat_data)

        assert action == HistoryNotificationAction.IGNORE
        assert data is None

    def test_ignore_empty_heartbeat(self):
        """Test that empty heartbeat data is handled."""
        adapter = BleCommunicationBleak()
        # Empty data with first byte 0x05
        heartbeat_data = bytearray([0x05])

        action, data = adapter._process_history_notification(heartbeat_data)

        assert action == HistoryNotificationAction.IGNORE
        assert data is None

    def test_detect_end_marker(self):
        """Test detection of end-of-logs marker.

        Reference: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        End marker: 0x3A 3A 10 0xFFFFFFFF FFFFFFFF (all 0xFF)
        """
        adapter = BleCommunicationBleak()
        # End marker from official docs: 0x3A 3A 10 with payload all 0xFF
        end_marker = bytearray.fromhex("3a3a10ffffffffffffffff")

        action, data = adapter._process_history_notification(end_marker)

        assert action == HistoryNotificationAction.END
        assert data == end_marker

    def test_detect_end_marker_variations(self):
        """Test end marker detection with different lengths."""
        adapter = BleCommunicationBleak()
        # End marker with minimum length (3 bytes + all 0xFF)
        end_marker_short = bytearray([0x3A, 0x3A, 0x10, 0xFF, 0xFF, 0xFF])

        action, data = adapter._process_history_notification(end_marker_short)

        assert action == HistoryNotificationAction.END
        assert data == end_marker_short

    def test_detect_error_packet(self):
        """Test detection of error packet.

        Reference: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        Error message: Header type 0xF0 with payload 0xFF, e.g. 0x30 30 F0 FF FF FF FF FF FF FF FF
        """
        adapter = BleCommunicationBleak()
        # Error packet from official docs: 0x30 30 F0 FF FF FF FF FF FF FF FF
        error_data = bytearray.fromhex("3030f0ffffffffffffffff")

        action, data = adapter._process_history_notification(error_data)

        assert action == HistoryNotificationAction.ERROR
        assert data == error_data

    def test_error_packet_different_first_bytes(self):
        """Test error packet detection with different first bytes."""
        adapter = BleCommunicationBleak()
        # Error packet can have different first bytes, but data[2] == 0xF0
        error_data = bytearray([0x3A, 0x30, 0xF0, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

        action, data = adapter._process_history_notification(error_data)

        assert action == HistoryNotificationAction.ERROR
        assert data == error_data

    def test_error_packet_too_short(self):
        """Test that error packet detection requires at least 11 bytes."""
        adapter = BleCommunicationBleak()
        # Too short to be an error packet (needs at least 11 bytes)
        short_data = bytearray([0x30, 0x30, 0xF0, 0xFF, 0xFF])

        action, data = adapter._process_history_notification(short_data)

        # Should be treated as normal data, not error
        assert action == HistoryNotificationAction.DATA
        assert data == short_data

    def test_normal_temperature_data(self):
        """Test processing of normal temperature history data."""
        adapter = BleCommunicationBleak()
        # Normal temperature entry from official docs: 0x3A 30 10 5D57FEAD 000000098D
        temp_data = bytearray.fromhex("3a30105d57fead000000098d")

        action, data = adapter._process_history_notification(temp_data)

        assert action == HistoryNotificationAction.DATA
        assert data == temp_data

    def test_normal_humidity_data(self):
        """Test processing of normal humidity history data."""
        adapter = BleCommunicationBleak()
        # Normal humidity entry from official docs: 0x3A 31 10 5D57FEAD 000000098D
        humidity_data = bytearray.fromhex("3a31105d57fead000000098d")

        action, data = adapter._process_history_notification(humidity_data)

        assert action == HistoryNotificationAction.DATA
        assert data == humidity_data

    def test_normal_pressure_data(self):
        """Test processing of normal pressure history data."""
        adapter = BleCommunicationBleak()
        # Normal pressure entry from official docs: 0x3A 32 10 5D57FEAD 000000098D
        pressure_data = bytearray.fromhex("3a32105d57fead000000098d")

        action, data = adapter._process_history_notification(pressure_data)

        assert action == HistoryNotificationAction.DATA
        assert data == pressure_data

    def test_empty_data(self):
        """Test handling of empty data."""
        adapter = BleCommunicationBleak()
        empty_data = bytearray()

        action, data = adapter._process_history_notification(empty_data)

        # Empty data should be treated as normal data (will be filtered by decoder)
        assert action == HistoryNotificationAction.DATA
        assert data == empty_data

    def test_short_data(self):
        """Test handling of short data (less than 3 bytes)."""
        adapter = BleCommunicationBleak()
        short_data = bytearray([0x3A, 0x30])

        action, data = adapter._process_history_notification(short_data)

        # Short data should be treated as normal data
        assert action == HistoryNotificationAction.DATA
        assert data == short_data

    def test_data_not_end_marker_if_not_all_ff(self):
        """Test that data is not treated as end marker if bytes after index 3 are not all 0xFF."""
        adapter = BleCommunicationBleak()
        # Has 0x3A 0x3A 0x10 but not all 0xFF after
        data = bytearray([0x3A, 0x3A, 0x10, 0xFF, 0xFF, 0x00, 0xFF])

        action, data_result = adapter._process_history_notification(data)

        assert action == HistoryNotificationAction.DATA
        assert data_result == data

    def test_data_not_error_if_f0_not_at_index_2(self):
        """Test that data is not treated as error if 0xF0 is not at index 2."""
        adapter = BleCommunicationBleak()
        # Has 0xF0 but not at index 2
        data = bytearray([0x30, 0xF0, 0x30, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

        action, data_result = adapter._process_history_notification(data)

        assert action == HistoryNotificationAction.DATA
        assert data_result == data

    def test_multiple_notifications_sequence(self):
        """Test processing a sequence of different notification types."""
        adapter = BleCommunicationBleak()

        # Heartbeat (should be ignored)
        action, data = adapter._process_history_notification(bytearray([0x05, 0x01]))
        assert action == HistoryNotificationAction.IGNORE
        assert data is None

        # Normal temperature data
        temp_data = bytearray.fromhex("3a30105d57fead000000098d")
        action, data = adapter._process_history_notification(temp_data)
        assert action == HistoryNotificationAction.DATA
        assert data == temp_data

        # Normal humidity data
        humidity_data = bytearray.fromhex("3a31105d57fead000000098d")
        action, data = adapter._process_history_notification(humidity_data)
        assert action == HistoryNotificationAction.DATA
        assert data == humidity_data

        # End marker
        end_marker = bytearray.fromhex("3a3a10ffffffffffffffff")
        action, data = adapter._process_history_notification(end_marker)
        assert action == HistoryNotificationAction.END
        assert data == end_marker
