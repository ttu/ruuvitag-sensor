from typing import Iterator, List
from ruuvitag_sensor.adapters import BleCommunication
from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData


class BleCommunicationDummy(BleCommunication):
    """TODO: Find some working BLE implementation for Windows and OSX"""

    @staticmethod
    def get_first_data(mac: str, bt_device: str = '') -> RawData:
        return '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'

    @staticmethod
    def get_data(blacklist: List[str] = [], bt_device: str = '') -> Iterator[MacAndRawData]:
        dummy_data = [
            ('DU:MM:YD:AT:A9:3D',
             '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('NO:TS:UP:PO:RT:ED',
             '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD')
        ]

        for data in dummy_data:
            yield data
