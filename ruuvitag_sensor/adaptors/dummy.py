from ruuvitag_sensor.adaptors import BleCommunication

class BleCommunicationDummy(BleCommunication):
    """TODO: Find some working BLE implementation for Windows and OSX"""

    @staticmethod
    def get_data(mac, bt_device=''):
        return '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'

    @staticmethod
    def get_datas(blacklist=[], bt_device=''):
        datas = [
            ('75:B6:68:32:18:49', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('36:9B:7E:16:18:9B', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD')
        ]

        for data in datas:
            yield data
