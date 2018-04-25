import abc
import logging
import os
import subprocess
import sys

from queue import Queue
from bleson import get_provider, Observer

log = logging.getLogger(__name__)


# Eddystone Protocol specification
# https://github.com/google/eddystone/blob/master/protocol-specification.md
# Bluetooth Service UUID used by Eddystone
#  16bit: 0xfeaa (65194)
#  64bit: 0000FEAA-0000-1000-8000-00805F9B34FB


class BleCommunication(object):
    '''Bluetooth LE communication'''
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
    '''TODO: Find some working BLE implementation for Windows and OSX'''

    @staticmethod
    def get_data(mac, bt_device=''):
        return '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'

    @staticmethod
    def get_datas(blacklist=[], bt_device=''):
        datas = [
            ('BC:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('AA:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD')
        ]

        for data in datas:
            yield data


class BleCommunicationNix(BleCommunication):
    '''Bluetooth LE communication for Linux'''

    @staticmethod
    def start(bt_device=''):
        '''
        Attributes:
           device (string): BLE device (default hci0)
        '''
        # import ptyprocess here so as long as all implementations are in the same file, all will work
        import ptyprocess

        if not bt_device:
            bt_device = 'hci0'

        log.info('Start receiving broadcasts (device %s)', bt_device)
        DEVNULL = subprocess.DEVNULL if sys.version_info >= (3, 3) else open(os.devnull, 'wb')

        subprocess.call('sudo hciconfig %s reset' % bt_device, shell=True, stdout=DEVNULL)
        hcitool = subprocess.Popen(['sudo', '-n', 'hcitool', 'lescan', '--duplicates'], stdout=DEVNULL)
        hcidump = ptyprocess.PtyProcess.spawn(['sudo', '-n', 'hcidump', '--raw'])
        return (hcitool, hcidump)

    @staticmethod
    def stop(hcitool, hcidump):
        # import psutil here so as long as all implementations are in the same file, all will work
        import psutil

        log.info('Stop receiving broadcasts')

        def kill_child_processes(parent_pid):
            try:
                parent = psutil.Process(parent_pid)
            except psutil.NoSuchProcess:
                return

            for process in parent.children(recursive=True):
                subprocess.call(['sudo', '-n', 'kill', '-s', 'SIGINT', str(process.pid)])

        kill_child_processes(hcitool.pid)
        subprocess.call(['sudo', '-n', 'kill', '-s', 'SIGINT', str(hcitool.pid)])
        kill_child_processes(hcidump.pid)
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


class BleCommunicationBleson(BleCommunication):
    '''Bluetooth LE communication with Bleson'''

    @staticmethod
    def start(bt_device=''):
        '''
        Attributes:
           device (string): BLE device (default 0)
        '''

        if not bt_device:
            bt_device = 0
        else:
            # Old communication used hci0 etc.
            bt_device = bt_device.replace('hci', '')

        log.info('Start receiving broadcasts (device %s)', bt_device)

        q = Queue()

        # TODO: Should do this on own process?
        adapter = get_provider().get_adapter(int(bt_device))
        observer = Observer(adapter)
        observer.on_advertising_data = q.put
        observer.start()

        return (observer, q)

    @staticmethod
    def stop(observer):
        observer.stop()

    @staticmethod
    def get_lines(queue):
        try:
            while True:
                next_item = queue.get(True, None)
                yield next_item
        except KeyboardInterrupt as ex:
            return
        except Exception as ex:
            log.info(ex)
            return

    @staticmethod
    def get_datas(blacklist=[], bt_device=''):
        (observer, queue) = BleCommunicationBleson.start(bt_device)

        for line in BleCommunicationBleson.get_lines(queue):
            try:
                reversed_mac = line.address.address
                mac = ':'.join(reversed(reversed_mac.split(':')))
                if mac in blacklist:
                    continue

                yield (mac, line.service_data or line.mfg_data)
            except GeneratorExit:
                break
            except:
                continue

        BleCommunicationBleson.stop(observer)

    @staticmethod
    def get_data(mac, bt_device=''):
        data = None
        data_iter = BleCommunicationBleson.get_datas(bt_device)

        for data in data_iter:
            if mac == data[0]:
                log.info('Data found')
                data_iter.send(StopIteration)
                data = data[1]
                break

        return data
