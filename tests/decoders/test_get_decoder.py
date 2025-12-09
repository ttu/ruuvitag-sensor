from unittest import TestCase

from ruuvitag_sensor.decoder import (
    Df3Decoder,
    Df5Decoder,
    Df6Decoder,
    DfE1Decoder,
    UrlDecoder,
    get_decoder,
)


class TestGetDecoder(TestCase):
    """Test get_decoder function."""

    def test_getcorrectdecoder(self):
        dec = get_decoder(2)
        self.assertIsInstance(dec, UrlDecoder)
        dec = get_decoder(3)
        self.assertIsInstance(dec, Df3Decoder)
        dec = get_decoder(5)
        self.assertIsInstance(dec, Df5Decoder)
        dec = get_decoder(6)
        self.assertIsInstance(dec, Df6Decoder)
        dec = get_decoder("E1")
        self.assertIsInstance(dec, DfE1Decoder)
        # Test unknown format raises ValueError
        with self.assertRaises(ValueError) as context:
            get_decoder(99)
        self.assertIn("Unknown data format: 99", str(context.exception))
