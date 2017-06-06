import abc
import subprocess
import sys
import os
import logging

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
    def get_data(mac):
        pass

    @staticmethod
    @abc.abstractmethod
    def get_datas():
        pass


class BleCommunicationDummy(BleCommunication):
    '''TODO: Find some working BLE implementation for Windows and OSX'''

    @staticmethod
    def get_data(mac):
        return '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'

    @staticmethod
    def get_datas():
        datas = [
            ('BC:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD'),
            ('AA:2C:6A:1E:59:3D', '1E0201060303AAFE1616AAFE10EE037275752E76692F23416A7759414D4663CD')
        ]

        for data in datas:
            yield data


class BleCommunicationNix(BleCommunication):
    '''Bluetooth LE communication for Linux'''

    @staticmethod
    def start():
        log.info('Start receiving broadcasts')
        DEVNULL = subprocess.DEVNULL if sys.version_info >= (3, 3) else open(os.devnull, 'wb')

        subprocess.call('sudo hciconfig hci0 reset', shell=True, stdout=DEVNULL)
        hcitool = subprocess.Popen(['sudo', '-n', 'hcitool', 'lescan', '--duplicates'], stdout=DEVNULL)
        hcidump = subprocess.Popen(['sudo', '-n', 'hcidump', '--raw'], stdout=subprocess.PIPE)
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
        subprocess.call(['sudo', '-n', 'kill', '-s', 'SIGINT', str(hcidump.pid)])

    @staticmethod
    def get_lines(hcidump):
        data = None
        try:
            for line in hcidump.stdout:
                line = line.decode()
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
    def get_datas():
        procs = BleCommunicationNix.start()

        data = None
        for line in BleCommunicationNix.get_lines(procs[1]):
            try:
                found_mac = line[14:][:12]
                reversed_mac = ''.join(
                    reversed([found_mac[i:i + 2] for i in range(0, len(found_mac), 2)]))
                mac = ':'.join(a + b for a, b in zip(reversed_mac[::2], reversed_mac[1::2]))
                data = line[26:]
                yield (mac, data)
            except GeneratorExit:
                break
            except:
                continue

        BleCommunicationNix.stop(procs[0], procs[1])

    @staticmethod
    def get_data(mac):
        data = None
        data_iter = BleCommunicationNix.get_datas()
        for data in data_iter:
            if mac == data[0]:
                log.info('Data found')
                data_iter.send(StopIteration)
                data = data[1]
                break

        return data
