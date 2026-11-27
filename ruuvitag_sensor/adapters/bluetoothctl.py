import logging
import os
import subprocess
import sys
import time
from typing import Generator, List

from ruuvitag_sensor.adapters import BleCommunication
from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData

log = logging.getLogger(__name__)


class BleCommunicationBluetoothctl(BleCommunication):
    """Bluetooth LE communication using bluetoothctl for Linux"""

    @staticmethod
    def start(bt_device=""):
        """
        Attributes:
           device (string): BLE device (default hci0)
        """
        if not bt_device:
            bt_device = "hci0"

        is_root = os.getuid() == 0

        log.info("Start receiving broadcasts (device %s)", bt_device)
        DEVNULL = subprocess.DEVNULL

        def reset_ble_adapter():
            cmd = f"bluetoothctl -- power off && bluetoothctl -- power on"
            log.info("FYI: Calling a process%s: %s", "" if is_root else " with sudo", cmd)

            cmd = f"sudo {cmd}" if not is_root else cmd
            return subprocess.call(cmd, shell=True, stdout=DEVNULL)

        def start_with_retry(func, try_count, interval, msg):
            retcode = func()
            if retcode != 0 and try_count > 0:
                log.info(msg)
                time.sleep(interval)
                return start_with_retry(func, try_count - 1, interval + interval, msg)
            return retcode

        retcode = start_with_retry(reset_ble_adapter, 3, 1, "Problem with bluetoothctl reset. Retry reset.")

        if retcode != 0:
            log.info("Problem with bluetoothctl reset. Exit.")
            sys.exit(1)

        cmd = ["bluetoothctl", "scan", "on"]
        log.info("FYI: Spawning process%s: %s", "" if is_root else " with sudo", " ".join(str(i) for i in cmd))

        if not is_root:
            cmd.insert(0, "sudo")
        bluetoothctl = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return (None, bluetoothctl)

    @staticmethod
    def stop(hcitool, bluetoothctl):
        log.info("Stop receiving broadcasts")
        bluetoothctl.terminate()
        bluetoothctl.wait()

    @staticmethod
    def get_lines(bluetoothctl):
        data = None
        try:
            while True:
                line = bluetoothctl.stdout.readline().decode()
                if line == "":
                    # EOF reached
                    raise Exception("EOF received from bluetoothctl")

                line = line.strip()
                log.debug("Read line from bluetoothctl: %s", line)
                if line.startswith("Device "):
                    log.debug("Yielding %s", data)
                    yield data
                    data = line[7:].replace(" ", "")
                elif data:
                    data += line.replace(" ", "")
        except KeyboardInterrupt:
            return
        except Exception as ex:
            log.info(ex)
            return

    @staticmethod
    def get_data(blacklist: List[str] = [], bt_device: str = "") -> Generator[MacAndRawData, None, None]:
        procs = BleCommunicationBluetoothctl.start(bt_device)
        data = None
        for line in BleCommunicationBluetoothctl.get_lines(procs[1]):
            log.debug("Parsing line %s", line)
            try:
                # Make sure we're in upper case
                line = line.upper()  # noqa: PLW2901
                # We're interested in LE meta events, sent by Ruuvitags.
                # Those start with "DEVICE", followed by a MAC address.

                if not line.startswith("DEVICE"):
                    log.debug("Not a LE meta packet")
                    continue

                # The following 6 bytes are the MAC address of the sender
                found_mac = line[7:24]
                mac = ":".join(a + b for a, b in zip(found_mac[::2], found_mac[1::2]))
                if mac in blacklist:
                    log.debug("MAC blacklisted: %s", mac)
                    continue
                data = line[24:]
                log.debug("MAC: %s, data: %s", mac, data)
                yield (mac, data)
            except GeneratorExit:
                break
            except Exception:
                continue

        BleCommunicationBluetoothctl.stop(procs[0], procs[1])

    @staticmethod
    def get_first_data(mac: str, bt_device: str = "") -> RawData:
        data = None
        data_iter = BleCommunicationBluetoothctl.get_data([], bt_device)
        for d in data_iter:
            if mac == d[0]:
                log.info("Data found")
                data_iter.close()
                data = d[1]
                break

        return data or ""
