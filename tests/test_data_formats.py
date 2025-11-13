from ruuvitag_sensor.data_formats import DataFormats


class TestDataFormats:
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
        # Test cases based on Ruuvi Air Data Format E1 specification
        # BLE advertisement structure: [total_len][chunks...][rssi]
        # Format E1 has 40 bytes of payload data
        # Chunk 1: 020106 (BLE flags)
        # Chunk 2: 2B FF9904e1[40 bytes of DFE1 data]
        # Total: 30 (48 bytes) + BC (RSSI)
        test_case = (
            "30020106 2BFF9904e1170c5668c79e0065007004bd11ca00c90a0213e0ac000000decdee110000000000cbb8334c884f BC"
        )
        test_case = test_case.replace(" ", "")  # Remove spaces for clarity
        encoded = DataFormats.convert_data(test_case)
        assert encoded is not None
        assert encoded[0] == "E1"
        assert encoded[1].startswith("e1")

    def test_get_data_format_6_valid_data(self):
        # Test cases based on Ruuvi Air Data Format 6 specification
        # BLE advertisement structure: [total_len][chunks...][rssi]
        # Format 6 has 20 bytes of payload data
        # Chunk 1: 020106 (BLE flags)
        # Chunk 2: 17 FF990406[20 bytes of DF6 data]
        # Total: 1C (28 bytes) + BC (RSSI)
        test_case = "1C020106 17FF990406170C5668C79E007000C90501D9FFCD004C884F BC"
        test_case = test_case.replace(" ", "")  # Remove spaces for clarity
        encoded = DataFormats.convert_data(test_case)
        assert encoded[0] == 6
        assert encoded[1] is not None
        assert encoded[1].startswith("06")

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
