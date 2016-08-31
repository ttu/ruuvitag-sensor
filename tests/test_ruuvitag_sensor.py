from unittest import TestCase

from ruuvitag_sensor.ruuvi import RuuviTagSensor


class TestRuuviTagSensor(TestCase):
    def test_tag_update_is_valid(self):
        tag = RuuviTagSensor('01:01', 'test_sensor')
        state1 = tag.update()
        state2 = tag.state()

        self.assertEqual(state1['elapsed'], 5)
        self.assertEqual(state1['temperature'], -48.3)
        self.assertEqual(state1['pressure'], 985.79)
        self.assertEqual(state1['humidity'], 10.5)
