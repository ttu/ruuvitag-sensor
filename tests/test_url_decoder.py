from unittest import TestCase

from ruuvitag_sensor.url_decoder import UrlDecoder


class TestUrlDecoder(TestCase):
    def test_decode_is_valid(self):
        decoder = UrlDecoder()
        data = decoder.get_data('67WG3vbgg')
        print(data)
        self.assertEqual(data['elapsed'], 5)
        self.assertEqual(data['temperature'], -48.3)
        self.assertEqual(data['pressure'], 985.79)
        self.assertEqual(data['humidity'], 10.5)
