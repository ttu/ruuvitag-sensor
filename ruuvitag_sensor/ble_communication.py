# from gattlib import DiscoveryService
# from gattlib import GATTRequester


class BleCommunication(object):
    '''Bluetooth LE communication'''

    def init(self):
        pass

    def get_data(self, mac):
        # req = GATTRequester(mac)
        # steps = req.read_by_handle(0x15)[0]
        return '67WG3vbgg'

    def find_ruuvitags(self):
        # service = DiscoveryService("hci0")
        # devices = service.discover(2)

        # for address, name in devices.items():
        #     print("name: {}, address: {}".format(name, address))
        pass
