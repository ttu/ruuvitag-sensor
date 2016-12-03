from unittest import TestCase
from unittest.mock import patch

from ruuvitag_sensor.ruuvi import RuuviTagSensor


class TestRuuviTagSensor(TestCase):

    def get_data(self, mac):
        return '0x0201060303AAFE1616AAFE10EE037275752E7669232A6843744641424644'

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationNix.get_data',
           get_data)
    @patch('ruuvitag_sensor.ble_communication.BleCommunicationWin.get_data',
           get_data)
    def test_tag_update_is_valid(self):
        tag = RuuviTagSensor('48-2C-6A-1E-59-3D', 'test_sensor')

        state = tag.state
        self.assertEqual(state, {})

        state = tag.update()
        self.assertEqual(state['elapsed'], 97)
        self.assertEqual(state['temperature'], 22)
        self.assertEqual(state['pressure'], 1012)
        self.assertEqual(state['humidity'], 22)

    def test_false_mac_raise_error(self):
        with self.assertRaises(ValueError):
            RuuviTagSensor('48-2C-6A-1E', 'test_sensor')

    def test_tag_correct_properties(self):
        orgMac = 'AA-2C-6A-1E-59-3D'
        orgName = 'mysensor'
        tag = RuuviTagSensor(orgMac, orgName)

        name = tag.name
        mac = tag.mac
        state = tag.state
        self.assertEqual(name, orgName)
        self.assertEqual(mac, orgMac)
        self.assertEqual(state, {})

    def get_ble_devices(self):
        return [
                ('AA-2C-6A-1E-59-3D', ''),
                ('BB-2C-6A-1E-59-3D', ''),
                ('CC-2C-6A-1E-59-3D', 'ruuvi_device'),
        ]

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationWin.find_ble_devices',
           get_ble_devices)
    def test_find_tags(self):
        tags = RuuviTagSensor.find_ruuvitags()
        self.assertEqual(3, len(tags))
        self.assertEqual('ruuvi_device', tags[2][1])