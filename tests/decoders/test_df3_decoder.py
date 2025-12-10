from ruuvitag_sensor.decoder import Df3Decoder


class TestDf3Decoder:
    def test_df3decode_is_valid(self):
        decoder = Df3Decoder()
        data = decoder.decode_data("03291A1ECE1EFC18F94202CA0B5300000000BB")

        assert data["temperature"] == 26.3
        assert data["pressure"] == 1027.66
        assert data["humidity"] == 20.5
        assert data["battery"] == 2899
        assert data["acceleration"] != 0
        assert data["acceleration_x"] == -1000
        assert data["acceleration_y"] != 0
        assert data["acceleration_z"] != 0

        data = decoder.decode_data("03291A1ECE1EFC18F94202CA0B53BB")
        assert data["temperature"] == 26.3
        assert data["pressure"] == 1027.66
        assert data["humidity"] == 20.5
        assert data["battery"] == 2899
        assert data["acceleration"] != 0
        assert data["acceleration_x"] == -1000
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
