# from gattlib import DiscoveryService
# from gattlib import GATTRequester

eddystoneUuid = "0000FEAA-0000-1000-8000-00805F9B34FB"


class BleCommunication(object):
    '''Bluetooth LE communication'''

    def init(self):
        pass

    @staticmethod
    def get_data(mac):
        # req = GATTRequester(mac)
        # data = req.read_by_uuid(eddystoneUuid)[0]
        return '67WG3vbgg'

    def find_ruuvitags(self):
        # service = DiscoveryService("hci0")
        # devices = service.discover(2)

        # for address, name in devices.items():
        #     print("name: {}, address: {}".format(name, address))
        pass
