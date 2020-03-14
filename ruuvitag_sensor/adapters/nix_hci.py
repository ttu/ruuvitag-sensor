import logging
import os
import subprocess
import sys
import time

from ruuvitag_sensor.adapters import BleCommunication

log = logging.getLogger(__name__)


class BleCommunicationNix(BleCommunication):
    """Bluetooth LE communication for Linux"""

    @staticmethod
    def start(bt_device=''):
        """
        Attributes:
           device (string): BLE device (default hci0)
        """
        # import ptyprocess here so as long as all implementations are in
        # the same file, all will work
        import ptyprocess

        if not bt_device:
            bt_device = 'hci0'

        log.info('Start receiving broadcasts (device %s)', bt_device)
        if sys.version_info >= (3, 3):
            DEVNULL = subprocess.DEVNULL
        else:
            open(os.devnull, 'wb')

        def reset_ble_adapter():
            log.info("FYI: Calling a process with sudo!")
            return subprocess.call(
                'sudo hciconfig %s reset' % bt_device,
                shell=True,
                stdout=DEVNULL)

        def start_with_retry(func, try_count, interval, msg):
            retcode = func()
            if retcode != 0 and try_count > 0:
                log.info(msg)
                time.sleep(interval)
                return start_with_retry(
                    func, try_count - 1, interval + interval, msg)
            return retcode

        retcode = start_with_retry(
            reset_ble_adapter,
            3, 1,
            'Problem with hciconfig reset. Retry reset.')

        if retcode != 0:
            log.info('Problem with hciconfig reset. Exit.')
            exit(1)

        log.info("FYI: Spawning 2 processes with sudo!")
        hcitool = ptyprocess.PtyProcess.spawn(
            ['sudo', '-n', 'hcitool', '-i', bt_device, 'lescan2', '--duplicates'])
        hcidump = ptyprocess.PtyProcess.spawn(
            ['sudo', '-n', 'hcidump', '-i', bt_device, '--raw'])
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
        except KeyboardInterrupt:
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
        data_iter = BleCommunicationNix.get_datas([], bt_device)
        for data in data_iter:
            if mac == data[0]:
                log.info('Data found')
                data_iter.send(StopIteration)
                data = data[1]
                break

        return data
