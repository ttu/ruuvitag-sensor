from unittest import TestCase

from ruuvitag_sensor.url_decoder import UrlDecoder


class TestUrlDecoder(TestCase):
    # TODO: Add cases  as arguments

    def test_decode_is_valid(self):
        decoder = UrlDecoder()
        data = decoder.decode_data('AjwYAMFc')

        self.assertEqual(data['temperature'], 24)
        self.assertEqual(data['pressure'], 995)
        self.assertEqual(data['humidity'], 30)

    def test_decode_is_valid_case2(self):
        decoder = UrlDecoder()
        data = decoder.decode_data('AjgbAMFc')

        self.assertEqual(data['temperature'], 27)
        self.assertEqual(data['pressure'], 995)
        self.assertEqual(data['humidity'], 28)
