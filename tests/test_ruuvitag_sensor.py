from unittest import TestCase
from mock import patch, MagicMock

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.ruuvitag import RuuviTag

# pylint: disable=W0613

class TestRuuviTagSensor(TestCase):

    def get_data(self, mac, bt_device):
        # https://ruu.vi/#AjwYAMFc
        data = '043E2A0201030157168974A5F41E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'
        return data[26:]

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationNix.get_data',
           get_data)
    @patch('ruuvitag_sensor.ble_communication.BleCommunicationDummy.get_data',
           get_data)
    def test_tag_update_is_valid(self):
        tag = RuuviTag('48:2C:6A:1E:59:3D')

        state = tag.state
        self.assertEqual(state, {})

        state = tag.update()
        self.assertEqual(state['temperature'], 24)
        self.assertEqual(state['pressure'], 995)
        self.assertEqual(state['humidity'], 30)

    def test_false_mac_raise_error(self):
        with self.assertRaises(ValueError):
            RuuviTag('48:2C:6A:1E')

    def test_tag_correct_properties(self):
        org_mac = 'AA:2C:6A:1E:59:3D'
        tag = RuuviTag(org_mac)

        mac = tag.mac
        state = tag.state
        self.assertEqual(mac, org_mac)
        self.assertEqual(state, {})

    def get_datas(self, blacklist=[], bt_device=''):
        datas = [
            ('AA:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('BB:2C:6A:1E:59:3D', 'some other device'),
            ('CC:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('DD:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('EE:2C:6A:1E:59:3D', '1F0201060303AAFE1716AAFE10F9037275752E76692F23416A5558314D417730C3'),
            ('FF:2C:6A:1E:59:3D', '1902010415FF990403291A1ECE1E02DEF94202CA0B5300000000BB'),
            ('00:2C:6A:1E:59:3D', '1902010415FF990403291A1ECE1E02DEF94202CA0B53BB'),
            ('11:2C:6A:1E:59:3D', '043E2B020100014F884C33B8CB1F0201061BFF99040512FC5394C37C0004FFFC040CAC364200CDCBB8334C884FC4')
        ]

        for data in datas:
            yield data

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationDummy.get_datas',
           get_datas)
    @patch('ruuvitag_sensor.ble_communication.BleCommunicationNix.get_datas',
           get_datas)
    def test_find_tags(self):
        tags = RuuviTagSensor.find_ruuvitags()
        self.assertEqual(7, len(tags))

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationDummy.get_datas',
           get_datas)
    @patch('ruuvitag_sensor.ble_communication.BleCommunicationNix.get_datas',
           get_datas)
    def test_get_data_for_sensors(self):
        macs = ['CC:2C:6A:1E:59:3D', 'DD:2C:6A:1E:59:3D', 'EE:2C:6A:1E:59:3D']
        data = RuuviTagSensor.get_data_for_sensors(macs, 4)
        self.assertEqual(3, len(data))
        self.assertTrue('CC:2C:6A:1E:59:3D' in data)
        self.assertTrue('DD:2C:6A:1E:59:3D' in data)
        self.assertTrue(data['CC:2C:6A:1E:59:3D']['temperature'] == 24.0)
        self.assertTrue(data['EE:2C:6A:1E:59:3D']['temperature'] == 25.12)
        self.assertTrue(data['EE:2C:6A:1E:59:3D']['identifier'] == '0')

    def test_convert_data_not_valid(self):
        encoded = RuuviTagSensor.convert_data('not_valid')
        self.assertIsNone(encoded[0])
        self.assertIsNone(encoded[1])

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationDummy.get_datas',
           get_datas)
    @patch('ruuvitag_sensor.ble_communication.BleCommunicationNix.get_datas',
           get_datas)
    def test_get_datas(self):
        datas = []
        RuuviTagSensor.get_datas(datas.append)
        self.assertEqual(7, len(datas))

    @patch('ruuvitag_sensor.ble_communication.BleCommunicationDummy.get_datas',
           get_datas)
    @patch('ruuvitag_sensor.ble_communication.BleCommunicationNix.get_datas',
           get_datas)
    def test_get_datas_with_macs(self):
        datas = []
        macs = ['CC:2C:6A:1E:59:3D', 'DD:2C:6A:1E:59:3D']
        RuuviTagSensor.get_datas(datas.append, macs)
        self.assertEqual(2, len(datas))
