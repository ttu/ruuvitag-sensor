from unittest import TestCase

from ruuvitag_sensor.data_formats import DataFormats

# pylint: disable=W0613

class TestDataFormats(TestCase):

    def test_convert_data_valid_data(self):
        test_cases = [
            ('1502010611FF990403651652CAE900080018041C0C8BC6', 3, '03651652CAE900080018041C0C8BC6'),
            ('1502010611FF990403411540C84AFC72FE2FFFC50B89C6', 3, '03411540C84AFC72FE2FFFC50B89C6')
        ]
        for x, data_format, result in test_cases:
            encoded = DataFormats.convert_data(x)
            print(encoded[1])
            self.assertEqual(data_format, encoded[0])
            self.assertEqual(result, encoded[1])

    def test_convert_data_not_valid_binary(self):
        data = b'\x99\x04\x03P\x15]\xceh\xfd\x88\x03\x05\x00\x1b\x0c\x13\x00\x00\x00\x00'
        encoded = DataFormats.convert_data(data)
        self.assertIsNone(encoded[0])
        self.assertIsNone(encoded[1])

    def test_convert_data_not_valid(self):
        encoded = DataFormats.convert_data('not_valid')
        self.assertIsNone(encoded[0])
        self.assertIsNone(encoded[1])

    def test_get_data_format_3_valid_data(self):
        test_cases = [
            '1502010611FF990403651652CAE900080018041C0C8BC6',
            '1502010611FF990403411540C84AFC72FE2FFFC50B89C6',
        ]
        for x in test_cases:
            encoded = DataFormats._get_data_format_3(x)
            self.assertIsNotNone(encoded)

    def test_get_data_format_5_valid_data(self):
        test_cases = [
            '1F0201061BFF990405138A5F92C4F3FFE4FFDC0414C4F6EC29BBE62EB92E73E5BC',
            '1F0201061BFF990405138A5F61C4F0FFE4FFDC0414C5B6EC29B3E62EB92E73E5BC',
        ]
        for x in test_cases:
            encoded = DataFormats._get_data_format_5(x)
            self.assertIsNotNone(encoded)

    def test_get_data_format_2and4_valid_data(self):
        test_cases = [
            '1F0201060303AAFE1716AAFE10F6037275752E76692F234248415A414D576F77C9',
            '1F0201060303AAFE1716AAFE10F6037275752E76692F234248415A414D576F77C8',
            '1E0201060303AAFE1616AAFE10EE037275752E76692F23416E4159414D5645CC',
            '1E0201060303AAFE1616AAFE10EE037275752E76692F23416E4159414D5645C9'
        ]
        for x in test_cases:
            encoded = DataFormats._get_data_format_2and4(x)
            self.assertIsNotNone(encoded)
