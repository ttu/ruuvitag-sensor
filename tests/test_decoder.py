from unittest import TestCase

from ruuvitag_sensor.decoder import Df3Decoder, Df5Decoder, UrlDecoder, get_decoder, parse_mac


class TestDecoder(TestCase):
    def test_getcorrectdecoder(self):
        dec = get_decoder(2)
        self.assertIsInstance(dec, UrlDecoder)
        dec = get_decoder(3)
        self.assertIsInstance(dec, Df3Decoder)

    def test_decode_is_valid(self):
        decoder = UrlDecoder()
        data = decoder.decode_data("AjwYAMFc")

        assert data["temperature"] == 24
        assert data["pressure"] == 995
        assert data["humidity"] == 30
        assert data["identifier"] is None

    def test_decode_is_valid_case2(self):
        decoder = UrlDecoder()
        data = decoder.decode_data("AjgbAMFc")

        assert data["temperature"] == 27
        assert data["pressure"] == 995
        assert data["humidity"] == 28
        assert data["identifier"] is None

    def test_decode_is_valid_weatherstation_2017_04_12(self):
        decoder = UrlDecoder()
        data = decoder.decode_data("AjUX1MAw0")

        assert data["temperature"] == 25.12
        assert data["pressure"] == 992.0
        assert data["humidity"] == 26.5
        assert data["identifier"] == "0"

    def test_df3decode_is_valid(self):
        decoder = Df3Decoder()
        data = decoder.decode_data("03291A1ECE1EFC18F94202CA0B5300000000BB")

        assert data["temperature"], 26.3
        assert data["pressure"], 1027.66
        assert data["humidity"], 20.5
        assert data["battery"], 2899
        assert data["acceleration"] != 0
        assert data["acceleration_x"], -1000
        assert data["acceleration_y"] != 0
        assert data["acceleration_z"] != 0

        data = decoder.decode_data("03291A1ECE1EFC18F94202CA0B53BB")
        assert data["temperature"], 26.3
        assert data["pressure"], 1027.66
        assert data["humidity"], 20.5
        assert data["battery"], 2899
        assert data["acceleration"] != 0
        assert data["acceleration_x"], -1000
        assert data["acceleration_y"] != 0
        assert data["acceleration_z"] != 0

    def test_df3decode_is_valid_notNone(self):
        test_cases = [
            "1502010611FF990403411540C84AFC72FE2FFFC50B89C6",
            "1502010611FF990403411544C850FC72FE2FFFC60B89B9",
            "1502010611FF990403411540C855FC72FE2FFFC30B83C7",
            "1502010611FF990403411539C842FC72FE2FFFC60B89C5",
            "1502010611FF990403421534C813FC72FE2FFFC50B8FD5",
            "1502010611FF990403441536C810FC72FE2FFFC70B83C7",
        ]
        decoder = Df3Decoder()
        for x in test_cases:
            data = decoder.decode_data(x)
            assert data is not None

    def test_df3decode_is_valid_max_values(self):
        decoder = Df3Decoder()
        humidity = "C8"
        temp = "7F63"
        pressure = "FFFF"
        accX = "03E8"
        accY = "03E8"
        accZ = "03E8"
        batt = "FFFF"
        data = decoder.decode_data(f"03{humidity}{temp}{pressure}{accX}{accY}{accZ}{batt}00000000BB")

        assert data["temperature"] == 127.99
        assert data["pressure"] == 1155.35
        assert data["humidity"] == 100.0
        assert data["battery"] == 65535
        assert data["acceleration_x"] == 1000
        assert data["acceleration_y"] == 1000
        assert data["acceleration_z"] == 1000
        assert data["acceleration"] != 0

    def test_df3decode_is_valid_min_values(self):
        decoder = Df3Decoder()
        humidity = "00"
        temp = "FF63"
        pressure = "0000"
        accX = "FC18"
        accY = "FC18"
        accZ = "FC18"
        batt = "0000"
        data = decoder.decode_data(f"03{humidity}{temp}{pressure}{accX}{accY}{accZ}{batt}00000000BB")

        assert data["temperature"] == -127.99
        assert data["pressure"] == 500.0
        assert data["humidity"] == 0.0
        assert data["battery"] == 0
        assert data["acceleration_x"] == -1000
        assert data["acceleration_y"] == -1000
        assert data["acceleration_z"] == -1000
        assert data["acceleration"] != 0

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

    def test_parse_df5_mac(self):
        mac_payload = "e62eb92e73e5"
        mac = "E6:2E:B9:2E:73:E5"

        parsed = parse_mac(5, mac_payload)
        assert parsed == mac
