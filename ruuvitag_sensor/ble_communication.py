import abc
import logging
import os
import subprocess
import sys

log = logging.getLogger(__name__)


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


class BleCommunicationDummy(BleCommunication):
    """TODO: Find some working BLE implementation for Windows and OSX"""

    @staticmethod
    def get_data(mac, bt_device=''):
        return '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'

    @staticmethod
    def get_datas(blacklist=[], bt_device=''):
        datas = [
            ('DU:MM:YD:AT:A9:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('NO:TS:UP:PO:RT:ED', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD')
        ]

        for data in datas:
            yield data


class BleCommunicationNix(BleCommunication):
    """Bluetooth LE communication for Linux"""

    @staticmethod
    def start(bt_device=''):
        """
        Attributes:
           device (string): BLE device (default hci0)
        """
        # import ptyprocess here so as long as all implementations are in the same file, all will work
        import ptyprocess

        if not bt_device:
            bt_device = 'hci0'

        log.info('Start receiving broadcasts (device %s)', bt_device)
        DEVNULL = subprocess.DEVNULL if sys.version_info >= (3, 3) else open(os.devnull, 'wb')

        subprocess.call('sudo hciconfig %s reset' % bt_device, shell=True, stdout=DEVNULL)
        hcitool = ptyprocess.PtyProcess.spawn(['sudo', '-n', 'hcitool', 'lescan', '--duplicates'])
        hcidump = ptyprocess.PtyProcess.spawn(['sudo', '-n', 'hcidump', '--raw'])
        return (hcitool, hcidump)

    @staticmethod
    def stop(hcitool, hcidump):
        log.info('Stop receiving broadcasts')
        hcitool.close()
        hcidump.close()

    @staticmethod
    def get_lines(hcidump):
        data = None
        try:
            while True:
                line = hcidump.readline().decode()
                if line.startswith('> '):
                    yield data
                    data = line[2:].strip().replace(' ', '')
                elif line.startswith('< '):
                    data = None
                else:
                    if data:
                        data += line.strip().replace(' ', '')
        except KeyboardInterrupt as ex:
            return
        except Exception as ex:
            log.info(ex)
            return

    @staticmethod
    def get_datas(blacklist=[], bt_device=''):
        procs = BleCommunicationNix.start(bt_device)

        data = None
        for line in BleCommunicationNix.get_lines(procs[1]):
            try:
                found_mac = line[14:][:12]
                reversed_mac = ''.join(
                    reversed([found_mac[i:i + 2] for i in range(0, len(found_mac), 2)]))
                mac = ':'.join(a + b for a, b in zip(reversed_mac[::2], reversed_mac[1::2]))
                if mac in blacklist:
                    continue
                data = line[26:]
                yield (mac, data)
            except GeneratorExit:
                break
            except:
                continue

        BleCommunicationNix.stop(procs[0], procs[1])

    @staticmethod
    def get_data(mac, bt_device=''):
        data = None
        data_iter = BleCommunicationNix.get_datas(bt_device)
        for data in data_iter:
            if mac == data[0]:
                log.info('Data found')
                data_iter.send(StopIteration)
                data = data[1]
                break

        return data
