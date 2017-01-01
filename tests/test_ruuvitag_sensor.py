from unittest import TestCase
from unittest.mock import patch

from ruuvitag_sensor.ruuvi import RuuviTagSensor


class TestRuuviTagSensor(TestCase):

    def get_data(self, mac):
        # https://ruu.vi/#AjwYAMFc
        data = '043E2A0201030157168974A5F41E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'
        return data[26:]

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationNix.get_data',
           get_data)
    @patch('ruuvitag_sensor.ble_communication.BleCommunicationDummy.get_data',
           get_data)
    def test_tag_update_is_valid(self):
        tag = RuuviTagSensor('48:2C:6A:1E:59:3D', 'test_sensor')

        state = tag.state
        self.assertEqual(state, {})

        state = tag.update()
        self.assertEqual(state['temperature'], 23)
        self.assertEqual(state['pressure'], 994)
        self.assertEqual(state['humidity'], 34)

    def test_false_mac_raise_error(self):
        with self.assertRaises(ValueError):
            RuuviTagSensor('48:2C:6A:1E', 'test_sensor')

    def test_tag_correct_properties(self):
        orgMac = 'AA:2C:6A:1E:59:3D'
        orgName = 'mysensor'
        tag = RuuviTagSensor(orgMac, orgName)

        name = tag.name
        mac = tag.mac
        state = tag.state
        self.assertEqual(name, orgName)
        self.assertEqual(mac, orgMac)
        self.assertEqual(state, {})

    def get_datas(self):
        return [
                ('AA:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
                ('BB:2C:6A:1E:59:3D', 'some other device'),
                ('CC:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
        ]

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationDummy.get_datas',
           get_datas)
    def test_find_tags(self):
        tags = RuuviTagSensor.find_ruuvitags()
        self.assertEqual(2, len(tags))

    def test_decode_data_not_valid(self):
        decoded = RuuviTagSensor.decode_data('not_valid')
        self.assertIsNone(decoded)
