from unittest import TestCase

from ruuvitag_sensor.url_decoder import UrlDecoder


class TestUrlDecoder(TestCase):
    # TODO: Add cases  as arguments

    def test_decode_is_valid(self):
        decoder = UrlDecoder()
        data = decoder.get_data('67WG3vbgg')

        self.assertEqual(data['elapsed'], 5)
        self.assertEqual(data['temperature'], -48.3)
        self.assertEqual(data['pressure'], 985.79)
        self.assertEqual(data['humidity'], 10.5)

    def test_decode_is_valid_case2(self):
        decoder = UrlDecoder()
        data = decoder.get_data('CtHsK0FKfA')

        self.assertEqual(data['elapsed'], 497)
        self.assertEqual(data['temperature'], 26)
        self.assertEqual(data['pressure'], 1016.58)
        self.assertEqual(data['humidity'], 56)
