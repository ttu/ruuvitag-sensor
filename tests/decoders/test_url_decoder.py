from ruuvitag_sensor.decoder import UrlDecoder


class TestUrlDecoder:
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
