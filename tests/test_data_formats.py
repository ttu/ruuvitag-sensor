from ruuvitag_sensor.data_formats import DataFormats


class TestDataFormats:

    @staticmethod
    def _get_data_format_e1(raw: str) -> RawSensorData:
        """
        Validate that data is from Ruuvi Air and is Data Format E1

        Returns:
            string: Sensor data
        """
        # Search of FF9904E1 (Manufacturer Specific Data (FF) /
        # Ruuvi Innovations ltd / Data format E1 (Extended v1)
        try:
            if "FF9904E1" not in raw:
                return None

            payload_start = raw.index("FF9904E1") + 6
            return raw[payload_start:]
        except Exception:
            return None

    def test_convert_data_valid_data(self):
        test_cases = [
            ("1502010611FF990403651652CAE900080018041C0C8BC6", 3, "03651652CAE900080018041C0C8B"),
            ("1502010611FF990403411540C84AFC72FE2FFFC50B89C6", 3, "03411540C84AFC72FE2FFFC50B89"),
        ]
        for x, data_format, result in test_cases:
            encoded = DataFormats.convert_data(x)
            print(encoded[1])
            assert data_format == encoded[0]
            assert result == encoded[1]

    def test_convert_data_not_valid_binary(self):
        data = b"\x99\x04\x03P\x15]\xceh\xfd\x88\x03\x05\x00\x1b\x0c\x13\x00\x00\x00\x00"
        encoded = DataFormats.convert_data(data)
        assert encoded[0] is None
        assert encoded[1] is None

    def test_convert_data_not_valid(self):
        encoded = DataFormats.convert_data("not_valid")
        assert encoded[0] is None
        assert encoded[1] is None

    def test_get_data_format_3_valid_data(self):
        test_cases = [
            "1502010611FF990403651652CAE900080018041C0C8BC6",
            "1502010611FF990403411540C84AFC72FE2FFFC50B89C6",
        ]
        for x in test_cases:
            encoded = DataFormats._get_data_format_3(x)
            assert encoded is not None

    def test_get_data_format_5_valid_data(self):
        test_cases = [
            "1F0201061BFF990405138A5F92C4F3FFE4FFDC0414C4F6EC29BBE62EB92E73E5BC",
            "1F0201061BFF990405138A5F61C4F0FFE4FFDC0414C5B6EC29B3E62EB92E73E5BC",
        ]
        for x in test_cases:
            encoded = DataFormats._get_data_format_5(x)
            assert encoded is not None

    def test_get_data_format_e1_valid_data(self):
        test_cases = [
            "E1170C5668C79E0065007004BD11CA00C90A0213E0AC000000DECDEE110000000000CBB8334C884F",
            "E17FFF9C40FFFE27102710271027109C40FAFADC28F0000000FFFFFE3F0000000000CBB8334C884F",
        ]
        for x in test_cases:
            encoded = _get_data_format_e1(x)
            assert encoded is not None

    def test_get_data_format_2and4_valid_data(self):
        test_cases = [
            "1F0201060303AAFE1716AAFE10F6037275752E76692F234248415A414D576F77C9",
            "1F0201060303AAFE1716AAFE10F6037275752E76692F234248415A414D576F77C8",
            "1E0201060303AAFE1616AAFE10EE037275752E76692F23416E4159414D5645CC",
            "1E0201060303AAFE1616AAFE10EE037275752E76692F23416E4159414D5645C9",
        ]
        for x in test_cases:
            encoded = DataFormats._get_data_format_2and4(x)
            assert encoded is not None

    def test_convert_data_too_short_data(self):
        test_case = "1E1107DC00240EE5A9E093F3A3B50100406E0B0952757576692042333634AC04"
        (data_format, data) = DataFormats.convert_data(test_case)
        assert data_format is None
        assert data == ""
