from ruuvitag_sensor.decoder import DfE1Decoder, get_decoder


class TestDfE1Decoder:
    def test_dfE1_decode_valid_data(self):
        """Test Data Format E1 decoder with valid data test vector from official docs"""
        decoder = DfE1Decoder()
        # Test vector from https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-e1
        # Raw binary data: 0xE1170C5668C79E0065007004BD11CA00C90A0213E0ACXXXXXXDECDEE10XXXXXXXXXXCBB8334C884F
        # (XX = Reserved, 0xFF)
        # VOC/NOx use LSB encoding: bits[8:1] in byte, bit[0] in FLAGS
        data = decoder.decode_data("E1170C5668C79E0065007004BD11CA00C90A0213E0ACFFFFFFDECDEE11FFFFFFFFFFCBB8334C884F")

        assert data is not None
        assert data["data_format"] == "E1"
        assert data["temperature"] == 29.5
        assert data["humidity"] == 55.3
        assert data["pressure"] == 1011.02
        assert data["pm_2_5"] == 11.2
        assert data["co2"] == 201
        assert data["voc"] == 20  # (0x0A << 1) | 0 = 20
        assert data["nox"] == 4  # (0x01 << 2) | 0 = 2
        assert data["luminosity"] == 13027.0
        assert data["measurement_sequence_number"] == 14601710
        assert data["calibration_in_progress"] is True
        assert data["mac"] == "CB:B8:33:4C:88:4F"

    def test_dfE1_decode_maximum_values(self):
        """Test Data Format E1 decoder with maximum values test vector"""
        decoder = DfE1Decoder()
        # Test vector from https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-e1
        # Raw binary data: 0xE17FFF9C40FFFE27102710271027109C40FAFADC28F0XXXXXXFFFFFE3FXXXXXXXXXXCBB8334C884F
        # (XX = Reserved, 0x00)
        # With LSB encoding: (0xFA << 1) | 0 = 500 for both VOC and NOx
        data = decoder.decode_data("E17FFF9C40FFFE27102710271027109C40FAFADC28F0000000FFFFFE300000000000CBB8334C884F")

        assert data is not None
        assert data["data_format"] == "E1"
        assert data["temperature"] == 163.835
        assert data["humidity"] == 100.0
        assert data["pressure"] == 1155.34
        assert data["pm_2_5"] == 1000.0
        assert data["co2"] == 40000
        assert data["voc"] == 500  # (0xFA << 1) | 0 = (250 << 1) = 500
        assert data["nox"] == 500  # (0xFA << 1) | 0 = (250 << 1) = 500
        assert data["luminosity"] == 144284.00
        assert data["measurement_sequence_number"] == 16777214
        assert data["calibration_in_progress"] is False
        assert data["mac"] == "CB:B8:33:4C:88:4F"

    def test_dfE1_decode_minimum_values(self):
        """Test Data Format E1 decoder with minimum values test vector"""
        decoder = DfE1Decoder()
        # Test vector from https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-E1
        # Raw binary data: 0xE1800100000000000000000000000000000000000000XXXXXX0000000XXXXXXXXXXXCBB8334C884F
        # (XX = Reserved, 0x00)
        data = decoder.decode_data("E1800100000000000000000000000000000000000000000000000000000000000000CBB8334C884F")

        assert data is not None
        assert data["data_format"] == "E1"
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
        assert data["mac"] == "CB:B8:33:4C:88:4F"

    def test_dfE1_decode_invalid_values(self):
        """Test Data Format E1 decoder with invalid/not available values"""
        decoder = DfE1Decoder()
        # Test vector from https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-E1
        # Raw binary data: 0xE18000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFXXXXXXFFFFFFFEXXXXXXXXXXFFFFFFFFFFFF
        # (XX = Reserved, 0x00)
        data = decoder.decode_data("E18000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000FFFFFFFE0000000000FFFFFFFFFFFF")

        assert data is not None
        assert data["data_format"] == "E1"
        assert data["temperature"] is None
        assert data["humidity"] is None
        assert data["pressure"] is None
        assert data["pm_2_5"] is None
        assert data["co2"] is None
        assert data["voc"] is None
        assert data["nox"] is None
        assert data["luminosity"] is None
        assert data["measurement_sequence_number"] is None
        assert data["calibration_in_progress"] is False
        assert data["mac"] == "FF:FF:FF:FF:FF:FF"

    def test_dfE1_decode_odd_voc_nox_values(self):
        """Test Data Format E1 decoder with odd VOC/NOX values"""
        decoder = DfE1Decoder()
        # Test with odd values where LSB bit is set
        # VOC=501: bits[8:1]=250 (0xFA), bit[0]=1 → FLAGS bit 6 = 1
        # NOx=503: bits[8:1]=251 (0xFB), bit[0]=1 → FLAGS bit 7 = 1
        # FLAGS = 0b11000001 = 0xC1 (bits 7,6 set + calibration bit 0)
        data = decoder.decode_data("E1170C5668C79E0065007004BD11CA00C9FAFB13E0AC000000DFFFFFC10000000000CBB8334C884F")

        assert data is not None
        assert data["data_format"] == "E1"
        assert data["voc"] == 501  # (250 << 1) | 1 = 501
        assert data["nox"] == 503  # (251 << 1) | 1 = 503
        assert data["calibration_in_progress"] is True

    def test_get_decoder_dfE1(self):
        """Test that get_decoder returns DfE1Decoder for data format E1"""
        decoder = get_decoder("E1")
        assert isinstance(decoder, DfE1Decoder)
