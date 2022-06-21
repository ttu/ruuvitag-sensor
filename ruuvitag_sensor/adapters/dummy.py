from ruuvitag_sensor.adapters import BleCommunication


class BleCommunicationDummy(BleCommunication):
    """TODO: Find some working BLE implementation for Windows and OSX"""

    @staticmethod
    def get_first_data(mac, bt_device=''):
        return '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'

    @staticmethod
    def get_data(blacklist=[], bt_device=''):
        dummy_data = [
            ('DU:MM:YD:AT:A9:3D',
             '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('NO:TS:UP:PO:RT:ED',
             '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD')
        ]

        for data in dummy_data:
            yield data
