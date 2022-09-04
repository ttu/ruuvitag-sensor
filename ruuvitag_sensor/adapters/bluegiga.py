import logging
import os
import sys
import time
from typing import Iterator, List, Tuple
import pygatt
import binascii
import threading
import os

from multiprocessing import Manager
from queue import Queue

from ruuvitag_sensor.adapters import BleCommunication

log = logging.getLogger(__name__)

class BleCommunicationBluegiga(BleCommunication):
    """Bluetooth LE communication for Bluegiga"""

    @staticmethod
    def get_first_data(mac: str, bt_device: str = '') -> str:
        if not bt_device:
            adapter = pygatt.BGAPIBackend()
        else:
            adapter = pygatt.BGAPIBackend(bt_device)

        def scan_received(devices, addr, packet_type):
            if mac and mac == addr:
                log.debug('Received data from device: %s %s', addr, packet_type)
                return True # stop scan

        reset = False if os.environ.get('BLUEGIGA_RESET', '').upper() == 'FALSE' else True
        adapter.start(reset=reset)
        log.debug('Start receiving broadcasts (device %s)', bt_device)
        try:
            devices = adapter.scan(timeout=60, active=False, scan_cb=scan_received)
            for dev in devices:
                if mac and mac ==  dev['address']:
                    log.debug('Result found for device %s', mac )
                    rawdata = dev['packet_data']['non-connectable_advertisement_packet']['manufacturer_specific_data']
                    hexa = binascii.hexlify(rawdata).decode("ascii").upper()
                    log.debug('Data found: %s', hexa)
                    return hexa
        finally:
            adapter.stop()

    @staticmethod
    def get_data(blacklist: List[str] = [], bt_device: str = '') -> Iterator[Tuple[str, str]]:
        m = Manager()
        q = m.Queue()

        # Use Manager dict to share data between processes
        shared_data = m.dict()
        shared_data['blacklist'] = blacklist
        shared_data['stop'] = False

        # Start background process
        scanner = threading.Thread(
            name='Bluegiga scanner',
            target=BleCommunicationBluegiga._run_get_data_background,
            args=[q, shared_data, bt_device])
        scanner.start()

        try:
            while True:
                while not q.empty():
                    data = q.get()
                    log.debug('Found data: %s', data)
                    yield data
                time.sleep(0.1)
                if not scanner.is_alive():
                    raise Exception('Bluegiga scanner is not alive')
        except GeneratorExit:
            pass
        except KeyboardInterrupt as ex:
            pass
        except Exception as ex:
            log.info(ex)

        log.debug('Stop')
        shared_data['stop'] = True
        scanner.join()
        log.debug('Exit')
        return

    @staticmethod
    def _run_get_data_background(queue, shared_data, bt_device):
        """
        Attributes:
           device (string): BLE device (default auto)
        """

        if bt_device:
            adapter = pygatt.BGAPIBackend(bt_device)
        else:
            adapter = pygatt.BGAPIBackend()

        reset = False if os.environ.get('BLUEGIGA_RESET', '').upper() == 'FALSE' else True
        adapter.start(reset=reset)
        try:
            while True:
                try:
                    if shared_data['stop']:
                        break
                    devices = adapter.scan(timeout=0.5, active=False, )
                    for dev in devices:
                        log.debug('received: %s', dev)
                        mac = str(dev['address'])
                        if mac and mac in shared_data['blacklist']:
                            log.debug('MAC blacklisted: %s', mac)
                            continue
                        try:
                            rawdata = dev['packet_data']['non-connectable_advertisement_packet']['manufacturer_specific_data']
                            log.debug('Received manufacturer data from %s: %s', mac, rawdata)
                            hexa = binascii.hexlify(rawdata).decode("ascii").upper()
                            queue.put((mac, hexa))
                        except KeyError:
                            pass

                    # Prevent endless loop if device data never found
                    # Remove when #81 is fixed
                    queue.put(('', ''))
                except GeneratorExit:
                    return
                except KeyboardInterrupt as ex:
                    return
        finally:
            log.debug('Stop scan')
            adapter.stop()
