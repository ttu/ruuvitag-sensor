import pytest

from ruuvitag_sensor.decoder import (
    Df3Decoder,
    Df5Decoder,
    Df6Decoder,
    DfE1Decoder,
    UrlDecoder,
    get_decoder,
)


class TestGetDecoder:
    """Test get_decoder function."""

    def test_getcorrectdecoder(self):
        dec = get_decoder(2)
        assert isinstance(dec, UrlDecoder)
        dec = get_decoder(3)
        assert isinstance(dec, Df3Decoder)
        dec = get_decoder(5)
        assert isinstance(dec, Df5Decoder)
        dec = get_decoder(6)
        assert isinstance(dec, Df6Decoder)
        dec = get_decoder("E1")
        assert isinstance(dec, DfE1Decoder)
        # Test unknown format raises ValueError
        with pytest.raises(ValueError, match="Unknown data format: 99"):
            get_decoder(99)
