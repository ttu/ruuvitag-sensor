from datetime import datetime, timezone
from unittest import TestCase

from ruuvitag_sensor.decoder import (
    Df3Decoder,
    Df5Decoder,
    Df6Decoder,
    DfE1Decoder,
    HistoryDecoder,
    UrlDecoder,
    get_decoder,
    parse_mac,
)


class TestDecoder(TestCase):
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

    def test_decode_is_valid(self):
        decoder = UrlDecoder()
        data = decoder.decode_data("AjwYAMFc")

        assert data["temperature"] == 24
        assert data["pressure"] == 995
        assert data["humidity"] == 30
        assert data["identifier"] is None

    def test_decode_is_valid_case2(self):
        decoder = UrlDecoder()
        data = decoder.decode_data("AjgbAMFc")

        assert data["temperature"] == 27
        assert data["pressure"] == 995
        assert data["humidity"] == 28
        assert data["identifier"] is None

    def test_decode_is_valid_weatherstation_2017_04_12(self):
        decoder = UrlDecoder()
        data = decoder.decode_data("AjUX1MAw0")

        assert data["temperature"] == 25.12
        assert data["pressure"] == 992.0
        assert data["humidity"] == 26.5
        assert data["identifier"] == "0"

    def test_df3decode_is_valid(self):
        decoder = Df3Decoder()
        data = decoder.decode_data("03291A1ECE1EFC18F94202CA0B5300000000BB")

        assert data["temperature"] == 26.3
        assert data["pressure"] == 1027.66
        assert data["humidity"] == 20.5
        assert data["battery"] == 2899
        assert data["acceleration"] != 0
        assert data["acceleration_x"] == -1000
        assert data["acceleration_y"] != 0
        assert data["acceleration_z"] != 0

        data = decoder.decode_data("03291A1ECE1EFC18F94202CA0B53BB")
        assert data["temperature"] == 26.3
        assert data["pressure"] == 1027.66
        assert data["humidity"] == 20.5
        assert data["battery"] == 2899
        assert data["acceleration"] != 0
        assert data["acceleration_x"] == -1000
        assert data["acceleration_y"] != 0
        assert data["acceleration_z"] != 0

    def test_df3decode_is_valid_notNone(self):
        test_cases = [
            "1502010611FF990403411540C84AFC72FE2FFFC50B89C6",
            "1502010611FF990403411544C850FC72FE2FFFC60B89B9",
            "1502010611FF990403411540C855FC72FE2FFFC30B83C7",
            "1502010611FF990403411539C842FC72FE2FFFC60B89C5",
            "1502010611FF990403421534C813FC72FE2FFFC50B8FD5",
            "1502010611FF990403441536C810FC72FE2FFFC70B83C7",
        ]
        decoder = Df3Decoder()
        for x in test_cases:
            data = decoder.decode_data(x)
            assert data is not None

    def test_df3decode_is_valid_max_values(self):
        decoder = Df3Decoder()
        humidity = "C8"
        temp = "7F63"
        pressure = "FFFF"
        accX = "03E8"
        accY = "03E8"
        accZ = "03E8"
        batt = "FFFF"
        data = decoder.decode_data(f"03{humidity}{temp}{pressure}{accX}{accY}{accZ}{batt}00000000BB")

        assert data["temperature"] == 127.99
        assert data["pressure"] == 1155.35
        assert data["humidity"] == 100.0
        assert data["battery"] == 65535
        assert data["acceleration_x"] == 1000
        assert data["acceleration_y"] == 1000
        assert data["acceleration_z"] == 1000
        assert data["acceleration"] != 0

    def test_df3decode_is_valid_min_values(self):
        decoder = Df3Decoder()
        humidity = "00"
        temp = "FF63"
        pressure = "0000"
        accX = "FC18"
        accY = "FC18"
        accZ = "FC18"
        batt = "0000"
        data = decoder.decode_data(f"03{humidity}{temp}{pressure}{accX}{accY}{accZ}{batt}00000000BB")

        assert data["temperature"] == -127.99
        assert data["pressure"] == 500.0
        assert data["humidity"] == 0.0
        assert data["battery"] == 0
        assert data["acceleration_x"] == -1000
        assert data["acceleration_y"] == -1000
        assert data["acceleration_z"] == -1000
        assert data["acceleration"] != 0

    def test_df5decode_is_valid(self):
        decoder = Df5Decoder()
        data_format = "05"
        temp = "12FC"
        humidity = "5394"
        pressure = "C37C"
        accX = "0004"
        accY = "FFFC"
        accZ = "040C"
        power_info = "AC36"
        movement_counter = "42"
        measurement_sequence = "00CD"
        mac = "CBB8334C884F"
        rssi = "C6"
        data = decoder.decode_data(
            f"{data_format}{temp}{humidity}{pressure}{accX}{accY}{accZ}{power_info}"
            f"{movement_counter}{measurement_sequence}{mac}{rssi}"
        )

        assert data["temperature"] == 24.30
        assert data["humidity"] == 53.49
        assert data["pressure"] == 1000.44
        assert data["acceleration_x"] == 4
        assert data["acceleration_y"] == -4
        assert data["acceleration_z"] == 1036
        assert data["tx_power"] == 4
        assert data["battery"] == 2977
        assert data["movement_counter"] == 66
        assert data["measurement_sequence_number"] == 205
        assert data["mac"] == "cbb8334c884f"
        assert data["rssi"] == -58

        # No RSSI case
        data = decoder.decode_data(
            f"{data_format}{temp}{humidity}{pressure}{accX}{accY}{accZ}{power_info}"
            f"{movement_counter}{measurement_sequence}{mac}"
        )

        assert data["rssi"] is None

    def test_parse_df5_mac(self):
        mac_payload = "e62eb92e73e5"
        mac = "E6:2E:B9:2E:73:E5"

        parsed = parse_mac(5, mac_payload)
        assert parsed == mac

    def test_history_decode_docs_temperature(self):
        # Data from: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        # 0x3A 30 10 5D57FEAD 000000098D
        sample_clean = ["3a", "30", "10", "5D", "57", "FE", "AD", "00", "00", "09", "8D"]
        sample_bytes = bytearray.fromhex("".join(sample_clean))
        decoder = HistoryDecoder()
        data = decoder.decode_data(sample_bytes)
        # 2019-08-13 13:18 24.45 C“
        assert data["temperature"] == 24.45
        # TODO: Check datetime if it is correct in docs
        assert (
            data["timestamp"] == datetime(2019, 8, 17, 13, 18, 37, tzinfo=timezone.utc).timestamp()
        )  # datetime(2019, 8, 13, 13, 18, 37)

    def test_history_decode_docs_humidity(self):
        # Data from: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        # 0x3A 31 10 5D57FEAD 000000098D
        sample_clean = ["3a", "31", "10", "5D", "57", "FE", "AD", "00", "00", "09", "8D"]
        sample_bytes = bytearray.fromhex("".join(sample_clean))
        decoder = HistoryDecoder()
        data = decoder.decode_data(sample_bytes)
        # 2019-08-13 13:18 24.45 RH-%
        assert data["humidity"] == 24.45
        # TODO: Check datetime if it is correct in docs
        assert (
            data["timestamp"] == datetime(2019, 8, 17, 13, 18, 37, tzinfo=timezone.utc).timestamp()
        )  # datetime(2019, 8, 13, 13, 18, 37)

    def test_history_decode_docs_pressure(self):
        # Data from: https://docs.ruuvi.com/communication/bluetooth-connection/nordic-uart-service-nus/log-read
        # 0x3A 32 10 5D57FEAD 000000098D
        sample_clean = ["3a", "32", "10", "5D", "57", "FE", "AD", "00", "00", "09", "8D"]
        sample_bytes = bytearray.fromhex("".join(sample_clean))
        decoder = HistoryDecoder()
        data = decoder.decode_data(sample_bytes)
        # 2019-08-13 13:18 2445 Pa
        assert data["pressure"] == 2445
        # TODO: Check datetime if it is correct in docs
        assert (
            data["timestamp"] == datetime(2019, 8, 17, 13, 18, 37, tzinfo=timezone.utc).timestamp()
        )  # datetime(2019, 8, 13, 13, 18, 37)

    def test_history_decode_real_samples(self):
        decoder = HistoryDecoder()

        # Test temperature data
        data = bytearray(b':0\x10g\x9d\xb5"\x00\x00\x08\xe3')
        result = decoder.decode_data(data)
        assert result is not None
        assert result["temperature"] == 22.75
        assert result["humidity"] is None
        assert result["pressure"] is None
        assert result["timestamp"] == datetime(2025, 2, 1, 5, 46, 10, tzinfo=timezone.utc).timestamp()

        # Test humidity data
        data = bytearray(b':1\x10g\x9d\xb5"\x00\x00\x10\x90')
        result = decoder.decode_data(data)
        assert result is not None
        assert result["humidity"] == 42.4
        assert result["temperature"] is None
        assert result["pressure"] is None
        assert result["timestamp"] == datetime(2025, 2, 1, 5, 46, 10, tzinfo=timezone.utc).timestamp()

        # Test pressure data
        data = bytearray(b':2\x10g\x9d\xb5"\x00\x01\x8b@')
        result = decoder.decode_data(data)
        assert result is not None
        assert result["pressure"] == 35648
        assert result["temperature"] is None
        assert result["humidity"] is None
        assert result["timestamp"] == datetime(2025, 2, 1, 5, 46, 10, tzinfo=timezone.utc).timestamp()

    def test_history_end_marker(self):
        decoder = HistoryDecoder()
        data = bytearray(b"::\x10\xff\xff\xff\xff\xff\xff\xff\xff")
        result = decoder.decode_data(data)
        assert result is None

    def test_history_decode_is_error(self):
        decoder = HistoryDecoder()

        error_cases = [
            bytearray(b";\x10g\x9b\xb2\xaf\x00\x00\x08\xac"),  # 0x3B
            bytearray(b"9\x10g\x9b\xb2\xaf\x00\x00\x08\xac"),  # 0x39
            bytearray(b"?\x10g\x9b\xb2\xaf\x00\x00\x08\xac"),  # 0x3F
            bytearray(b""),  # Empty data
            bytearray(b":"),  # Too short
            bytearray(b":\x10"),  # Incomplete data
        ]
        for error_data in error_cases:
            assert decoder.decode_data(error_data) is None, f"Should be error for data: {error_data!r}"

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
