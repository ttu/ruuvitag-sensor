import abc

eddystoneUuid = '0000FEAA-0000-1000-8000-00805F9B34FB'
ruuviStart = 'ruuvi_'


class BleCommunication(object):
    '''Bluetooth LE communication'''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_data(mac):
        pass

    @abc.abstractmethod
    def find_ruuvitags(self):
        pass


class BleCommunicationWin(BleCommunication):
    '''TODO: Find some working BLE implementation for Windows'''

    @staticmethod
    def get_data(mac):
        return '67WG3vbgg'

    @staticmethod
    def find_ruuvitags(self):
        pass


class BleCommunicationNix(BleCommunication):
    '''Bluetooth LE communication for Linux'''
    
    @staticmethod
    def get_data(mac):
        # Do imports inside functions so they are not loaded during init
        from gattlib import DiscoveryService
        from gattlib import GATTRequester

        req = GATTRequester(mac)
        data = req.read_by_uuid(eddystoneUuid)[0]
        return data

    @staticmethod
    def find_ruuvitags(self):
        # service = DiscoveryService("hci0")
        # devices = service.discover(2)

        # return [address, name for address, name in devices.items() if name.startsWth(ruuviPrefi)]
        # for address, name in devices.items():
        #     print("name: {}, address: {}".format(name, address))
        pass
