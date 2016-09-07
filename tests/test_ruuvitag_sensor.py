from unittest import TestCase
from unittest.mock import patch

from ruuvitag_sensor.ruuvi import RuuviTagSensor


class TestRuuviTagSensor(TestCase):

    def get_data(self, mac):
        return 'CtHsK0FKfA'

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationNix.get_data',
           get_data)
    @patch('ruuvitag_sensor.ble_communication.BleCommunicationWin.get_data',
           get_data)
    def test_tag_update_is_valid(self):
        tag = RuuviTagSensor('48-2C-6A-1E-59-3D', 'test_sensor')

        state = tag.state
        self.assertEqual(state, {})

        state = tag.update()
        self.assertEqual(state['elapsed'], 497)
        self.assertEqual(state['temperature'], 26)
        self.assertEqual(state['pressure'], 1016.58)
        self.assertEqual(state['humidity'], 56)

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
