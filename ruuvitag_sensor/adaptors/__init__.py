import abc


class BleCommunication(object):
    """Bluetooth LE communication"""
    __metaclass__ = abc.ABCMeta

    @staticmethod
    @abc.abstractmethod
    def get_data(mac, bt_device=''):
        pass

    @staticmethod
    @abc.abstractmethod
    def get_datas(blacklist=[], bt_device=''):
        pass
