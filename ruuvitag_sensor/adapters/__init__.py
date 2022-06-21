import abc


class BleCommunication(object):
    """Bluetooth LE communication"""
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    def get_first_data(mac, bt_device=''):
        pass

    @staticmethod
    @abc.abstractmethod
    def get_data(blacklist=[], bt_device=''):
        pass
