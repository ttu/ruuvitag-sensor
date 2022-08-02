import logging
import os
import subprocess
import sys
import time

from ruuvitag_sensor.adapters import BleCommunication

log = logging.getLogger(__name__)

# pylint: disable=duplicate-code


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
        import ptyprocess  # pylint: disable=import-outside-toplevel

        if not bt_device:
            bt_device = 'hci0'

        is_root = os.getuid() == 0

        log.info('Start receiving broadcasts (device %s)', bt_device)
        DEVNULL = subprocess.DEVNULL

        def reset_ble_adapter():
            cmd = f'hciconfig {bt_device} reset'
            log.info("FYI: Calling a process%s: %s",
                     "" if is_root else " with sudo", cmd)

            cmd = f"sudo {cmd}" if not is_root else cmd
            return subprocess.call(cmd, shell=True, stdout=DEVNULL)

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
            sys.exit(1)

        cmd = ['hcitool', '-i', bt_device, 'lescan2', '--duplicates', '--passive']
        log.info("FYI: Spawning process%s: %s",
                 "" if is_root else " with sudo", ' '.join(str(i) for i in cmd))

        if not is_root:
            cmd.insert(0, "sudo")
        hcitool = ptyprocess.PtyProcess.spawn(cmd)

        cmd = ['hcidump', '-i', bt_device, '--raw']
        log.info("FYI: Spawning process%s: %s",
                 "" if is_root else " with sudo", ' '.join(str(i) for i in cmd))

        if not is_root:
            cmd.insert(0, "sudo")
        hcidump = ptyprocess.PtyProcess.spawn(cmd)

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
                if line == '':
                    # EOF reached
                    raise Exception("EOF received from hcidump")

                line = line.strip()
                log.debug("Read line from hcidump: %s", line)
                if line.startswith('> '):
                    log.debug("Yielding %s", data)
                    yield data
                    data = line[2:].replace(' ', '')
                elif line.startswith('< '):
                    data = None
                else:
                    if data:
                        data += line.replace(' ', '')
        except KeyboardInterrupt:
            return
        except Exception as ex:
            log.info(ex)
            return

    @staticmethod
    def get_data(blacklist=[], bt_device=''):
        procs = BleCommunicationNix.start(bt_device)
        data = None
        for line in BleCommunicationNix.get_lines(procs[1]):
            log.debug("Parsing line %s", line)
            try:
                # Make sure we're in upper case
                line = line.upper()
                # We're interested in LE meta events, sent by Ruuvitags.
                # Those start with "043E", followed by a length byte.

                if not line.startswith("043E"):
                    log.debug("Not a LE meta packet")
                    continue

                # The third byte is the parameter length, this should cover
                # the length of the entire packet, minus the first three bytes.
                # Note that the data is in hex format, so uses two chars per
                # byte
                plen = int(line[4:6], 16)
                if plen != (len(line) / 2) - 3:
                    log.debug("Invalid parameter length")
                    continue

                # The following two bytes should be "0201", indicating
                # 02  LE Advertising report
                # 01  1 report

                if line[6:10] != "0201":
                    log.debug("Not a Ruuvi advertisement")
                    continue

                # The next four bytes indicate whether the endpoint is
                # connectable or not, and whether the MAC address is random
                # or not. Different tags set different values here, so
                # ignore those.

                # The following 6 bytes are the MAC address of the sender,
                # in reverse order

                found_mac = line[14:26]
                reversed_mac = ''.join(
                    reversed([found_mac[i:i + 2] for i in range(0, len(found_mac), 2)]))
                mac = ':'.join(a + b for a, b in zip(reversed_mac[::2], reversed_mac[1::2]))
                if mac in blacklist:
                    log.debug('MAC blacklisted: %s', mac)
                    continue
                data = line[26:]
                log.debug("MAC: %s, data: %s", mac, data)
                yield (mac, data)
            except GeneratorExit:
                break
            except Exception:
                continue

        BleCommunicationNix.stop(procs[0], procs[1])

    @staticmethod
    def get_first_data(mac, bt_device=''):
        data = None
        data_iter = BleCommunicationNix.get_data([], bt_device)
        for data in data_iter:
            if mac == data[0]:
                log.info('Data found')
                data_iter.send(StopIteration)
                data = data[1]
                break

        return data
