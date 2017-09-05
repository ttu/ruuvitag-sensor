from unittest import TestCase

from ruuvitag_sensor.decoder import get_decoder, UrlDecoder, Df3Decoder


class TestDecoder(TestCase):

    def test_getcorrectdecoder(self):
        dec = get_decoder(2)
        self.assertIsInstance(dec, UrlDecoder)
        dec = get_decoder(3)
        self.assertIsInstance(dec, Df3Decoder)

    def test_decode_is_valid(self):
        decoder = UrlDecoder()
        data = decoder.decode_data('AjwYAMFc')

        self.assertEqual(data['temperature'], 24)
        self.assertEqual(data['pressure'], 995)
        self.assertEqual(data['humidity'], 30)
        self.assertEqual(data['identifier'], None)

    def test_decode_is_valid_case2(self):
        decoder = UrlDecoder()
        data = decoder.decode_data('AjgbAMFc')

        self.assertEqual(data['temperature'], 27)
        self.assertEqual(data['pressure'], 995)
        self.assertEqual(data['humidity'], 28)
        self.assertEqual(data['identifier'], None)

    def test_decode_is_valid_weatherstation_2017_04_12(self):
        decoder = UrlDecoder()
        data = decoder.decode_data('AjUX1MAw0')

        self.assertEqual(data['temperature'], 25.12)
        self.assertEqual(data['pressure'], 992.0)
        self.assertEqual(data['humidity'], 26.5)
        self.assertEqual(data['identifier'], '0')

    def test_df3decode_is_valid(self):
        decoder = Df3Decoder()
        data = decoder.decode_data('03291A1ECE1EFC18F94202CA0B5300000000BB')

        self.assertEqual(data['temperature'], 26.3)
        self.assertEqual(data['pressure'], 1027.66)
        self.assertEqual(data['humidity'], 20.5)
        self.assertEqual(data['battery'], 2899)
        self.assertNotEqual(data['acceleration'], 0)
        self.assertEqual(data['acceleration_x'], -1000)
        self.assertNotEqual(data['acceleration_y'], 0)
        self.assertNotEqual(data['acceleration_z'], 0)

    def test_df3decode_temperature(self):
        decoder = Df3Decoder()
        humidity = '29'
        temp = 'FF00'
        pressure = 'CE1E'
        accX = 'FC18'
        accY = '03E8'
        accZ = '02CA'
        batt = '0B53'
        data = decoder.decode_data('03{humidity}{temp}{pressure}{accX}{accY}{accZ}{batt}00000000BB'.format(
            humidity=humidity, temp=temp, pressure=pressure, accX=accX, accY=accY, accZ=accZ, batt=batt))

        self.assertEqual(data['temperature'], -127.00)
        self.assertEqual(data['pressure'], 1027.66)
        self.assertEqual(data['humidity'], 20.5)
        self.assertEqual(data['battery'], 2899)
        self.assertNotEqual(data['acceleration'], 0)
        self.assertEqual(data['acceleration_x'], -1000)
        self.assertEqual(data['acceleration_y'], 1000)
        self.assertNotEqual(data['acceleration_z'], 0)
