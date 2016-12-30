import abc
import subprocess

# Eddystone Protocol specification
# https://github.com/google/eddystone/blob/master/protocol-specification.md
# Bluetooth Service UUID used by Eddystone
#  16bit: 0xfeaa (65194)
#  64bit: 0000FEAA-0000-1000-8000-00805F9B34FB


class BleCommunication(object):
    '''Bluetooth LE communication'''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_data(mac):
        pass

    @abc.abstractmethod
    def find_ble_devices():
        pass


class BleCommunicationDummy(BleCommunication):
    '''TODO: Find some working BLE implementation for Windows and OSX'''

    @staticmethod
    def get_data(mac):
        return '0x0201060303AAFE1616AAFE10EE037275752E7669232A6843744641424644'

    @staticmethod
    def find_ble_devices():
        return [
            ('BC:2C:6A:1E:59:3D', ''),
            ('AA:2C:6A:1E:59:3D', '')
        ]


class BleCommunicationNix(BleCommunication):
    '''Bluetooth LE communication for Linux'''

    @staticmethod
    def start():
        print('Start receiving broadcasts')
        return subprocess.Popen(['sudo', '-n', 'hcidump', '--raw'], stdout=subprocess.PIPE)

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
        except Exception as ex:
            print(ex)

    @staticmethod
    def stop(hcidump):
        print('Stop receiving broadcasts')
        subprocess.call(['sudo', 'kill', str(hcidump.pid), '-s', 'SIGINT'])

    @staticmethod
    def get_data(mac):
        hcidump = BleCommunicationNix.start()

        line_iter = BleCommunicationNix.get_lines(hcidump)
        for data in line_iter:
            try:
                reverse_mac = data[14:][:12]
                correct_mac = ''.join(
                    reversed([reverse_mac[i:i + 2] for i in range(0, len(reverse_mac), 2)]))
            except:
                continue

            if mac.replace(':', '') == correct_mac:
                line_iter.send(StopIteration)
                BleCommunicationNix.stop(hcidump)
                return data[26:]

    @staticmethod
    def find_ble_devices():
        pass
