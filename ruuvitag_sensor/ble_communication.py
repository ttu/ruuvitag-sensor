import abc

# Eddystone Protocol specification
# https://github.com/google/eddystone/blob/master/protocol-specification.md
# Bluetooth Service UUID used by Eddystone
#  16bit: 0xfeaa
#  64bit: 0000FEAA-0000-1000-8000-00805F9B34FB

eddystone_uuid = '0000FEAA-0000-1000-8000-00805F9B34FB'


class BleCommunication(object):
    '''Bluetooth LE communication'''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_data(mac):
        pass

    @abc.abstractmethod
    def find_ble_devices():
        pass


class BleCommunicationWin(BleCommunication):
    '''TODO: Find some working BLE implementation for Windows'''

    @staticmethod
    def get_data(mac):
        return '0x0201060303AAFE1616AAFE10EE037275752E7669232A6843744641424644'

    @staticmethod
    def find_ble_devices():
        return [
                ('BC-2C-6A-1E-59-3D', ''),
                ('AA-2C-6A-1E-59-3D', '')
        ]


class BleCommunicationNix(BleCommunication):
    '''Bluetooth LE communication for Linux'''

    @staticmethod
    def get_data(mac):
        # Do imports inside functions so they are not loaded during init
        from gattlib import GATTRequester

        req = GATTRequester(mac)
        data = req.read_by_uuid(eddystone_uuid)[0]
        return data

    @staticmethod
    def find_ble_devices():
        # Do imports inside functions so they are not loaded during init
        from gattlib import DiscoveryService

        service = DiscoveryService("hci0")
        devices = service.discover(2)
        return devices.items()
