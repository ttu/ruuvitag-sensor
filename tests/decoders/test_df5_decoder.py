from ruuvitag_sensor.decoder import Df5Decoder, parse_mac


class TestDf5Decoder:
    def test_df5decode_is_valid(self):
        decoder = Df5Decoder()
        data_format = "05"
        temp = "12FC"
        humidity = "5394"
        pressure = "C37C"
        accX = "0004"
        accY = "FFFC"
        accZ = "040C"
        power_info = "AC36"
        movement_counter = "42"
        measurement_sequence = "00CD"
        mac = "CBB8334C884F"
        rssi = "C6"
        data = decoder.decode_data(
            f"{data_format}{temp}{humidity}{pressure}{accX}{accY}{accZ}{power_info}"
            f"{movement_counter}{measurement_sequence}{mac}{rssi}"
        )

        assert data["temperature"] == 24.30
        assert data["humidity"] == 53.49
        assert data["pressure"] == 1000.44
        assert data["acceleration_x"] == 4
        assert data["acceleration_y"] == -4
        assert data["acceleration_z"] == 1036
        assert data["tx_power"] == 4
        assert data["battery"] == 2977
        assert data["movement_counter"] == 66
        assert data["measurement_sequence_number"] == 205
        assert data["mac"] == "cbb8334c884f"
        assert data["rssi"] == -58

        # No RSSI case
        data = decoder.decode_data(
            f"{data_format}{temp}{humidity}{pressure}{accX}{accY}{accZ}{power_info}"
            f"{movement_counter}{measurement_sequence}{mac}"
        )

        assert data["rssi"] is None

    def test_df5decode_zero_acceleration(self):
        """Test that acceleration magnitude is calculated correctly with zero values."""
        decoder = Df5Decoder()
        data_format = "05"
        temp = "12FC"
        humidity = "5394"
        pressure = "C37C"
        accX = "0000"  # Zero acceleration X
        accY = "0000"  # Zero acceleration Y
        accZ = "0000"  # Zero acceleration Z
        power_info = "AC36"
        movement_counter = "42"
        measurement_sequence = "00CD"
        mac = "CBB8334C884F"
        rssi = "C6"
        data = decoder.decode_data(
            f"{data_format}{temp}{humidity}{pressure}{accX}{accY}{accZ}{power_info}"
            f"{movement_counter}{measurement_sequence}{mac}{rssi}"
        )

        assert data["acceleration_x"] == 0
        assert data["acceleration_y"] == 0
        assert data["acceleration_z"] == 0
        assert data["acceleration"] == 0.0  # Magnitude should be 0.0, not None

    def test_parse_df5_mac(self):
        mac_payload = "e62eb92e73e5"
        mac = "E6:2E:B9:2E:73:E5"

        parsed = parse_mac(5, mac_payload)
        assert parsed == mac
