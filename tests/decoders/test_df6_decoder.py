from unittest import TestCase

from ruuvitag_sensor.decoder import Df6Decoder, get_decoder


class TestDf6Decoder(TestCase):
    def test_df6_decode_valid_data(self):
        """Test Data Format 6 decoder with valid data test vector from official docs"""
        decoder = Df6Decoder()
        # Test vector from https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-6
        # Raw binary data: 0x06170C5668C79E007000C90501D9XXCD004C884F (XX = Reserved, 0xFF)
        # VOC/NOx use LSB encoding: bits[8:1] in byte, bit[0] in FLAGS
        data = decoder.decode_data("06170C5668C79E007000C90501D9FFCD004C884F")

        assert data is not None
        assert data["data_format"] == 6
        assert data["temperature"] == 29.5
        assert data["humidity"] == 55.3
        assert data["pressure"] == 1011.02
        assert data["pm_2_5"] == 11.2
        assert data["co2"] == 201
        assert data["voc"] == 10  # (0x05 << 1) | 0 = 10
        assert data["nox"] == 2  # (0x01 << 1) | 0 = 2
        assert data["luminosity"] == 13026.67
        assert data["measurement_sequence_number"] == 205
        assert data["calibration_in_progress"] is False
        assert data["mac"] == "4c884f"

    def test_df6_decode_maximum_values(self):
        """Test Data Format 6 decoder with maximum values test vector"""
        decoder = Df6Decoder()
        # Test vector from https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-6
        # Raw binary data: 0x067FFF9C40FFFE27109C40FAFAFEXXFF074C8F4F (XX = Reserved, 0xFF)
        # With LSB encoding: (0xFA << 1) | 0 = 500 for both VOC and NOx
        data = decoder.decode_data("067FFF9C40FFFE27109C40FAFAFEFFFF074C8F4F")

        assert data is not None
        assert data["data_format"] == 6
        assert data["temperature"] == 163.835
        assert data["humidity"] == 100.0
        assert data["pressure"] == 1155.34
        assert data["pm_2_5"] == 1000.0
        assert data["co2"] == 40000
        assert data["voc"] == 500  # (0xFA << 1) | 0 = (250 << 1) = 500
        assert data["nox"] == 500  # (0xFA << 1) | 0 = (250 << 1) = 500
        assert data["luminosity"] == 65535.0
        assert data["measurement_sequence_number"] == 255
        assert data["calibration_in_progress"] is True
        assert data["mac"] == "4c8f4f"

    def test_df6_decode_minimum_values(self):
        """Test Data Format 6 decoder with minimum values test vector"""
        decoder = Df6Decoder()
        # Test vector from https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-6
        # Raw binary data: 0x0680010000000000000000000000XX00004C884F (XX = Reserved, 0xFF)
        data = decoder.decode_data("0680010000000000000000000000FF00004C884F")

        assert data is not None
        assert data["data_format"] == 6
        assert data["temperature"] == -163.835
        assert data["humidity"] == 0.0
        assert data["pressure"] == 500.0
        assert data["pm_2_5"] == 0.0
        assert data["co2"] == 0
        assert data["voc"] == 0
        assert data["nox"] == 0
        assert data["luminosity"] == 0.0
        assert data["measurement_sequence_number"] == 0
        assert data["calibration_in_progress"] is False
        assert data["mac"] == "4c884f"

    def test_df6_decode_invalid_values(self):
        """Test Data Format 6 decoder with invalid/not available values"""
        decoder = Df6Decoder()
        # Test vector from https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-6
        # Raw binary data: 0x068000FFFFFFFFFFFFFFFFFFFFFFFFXXFFFFFFFFFF (XX = Reserved, 0xFF)
        data = decoder.decode_data("068000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")

        assert data is not None
        assert data["data_format"] == 6
        assert data["temperature"] is None
        assert data["humidity"] is None
        assert data["pressure"] is None
        assert data["pm_2_5"] is None
        assert data["co2"] is None
        assert data["voc"] is None
        assert data["nox"] is None
        assert data["luminosity"] is None
        assert data["measurement_sequence_number"] == 255
        assert data["calibration_in_progress"] is True
        assert data["mac"] == "ffffff"

    def test_df6_decode_odd_voc_nox_values(self):
        """Test Data Format 6 decoder with odd VOC/NOX values"""
        decoder = Df6Decoder()
        # Test with odd values where LSB bit is set
        # VOC=501: bits[8:1]=250 (0xFA), bit[0]=1 → FLAGS bit 6 = 1
        # NOx=503: bits[8:1]=251 (0xFB), bit[0]=1 → FLAGS bit 7 = 1
        # FLAGS = 0b11000001 = 0xC1 (bits 7,6 set + calibration bit 0)
        data = decoder.decode_data("067FFF9C40FFFE27109C40FAFBFEFFFFC14C8F4F")

        assert data is not None
        assert data["data_format"] == 6
        assert data["voc"] == 501  # (250 << 1) | 1 = 501
        assert data["nox"] == 503  # (251 << 1) | 1 = 503
        assert data["calibration_in_progress"] is True

    def test_get_decoder_df6(self):
        """Test that get_decoder returns Df6Decoder for data format 6"""
        decoder = get_decoder(6)
        assert isinstance(decoder, Df6Decoder)
