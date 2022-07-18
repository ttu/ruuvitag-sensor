import sys
import logging
from multiprocessing import Manager, Process
from queue import Queue
import time

from bleson import get_provider, Observer

from ruuvitag_sensor.adapters import BleCommunication

log = logging.getLogger(__name__)

# pylint: disable=duplicate-code


class BleCommunicationBleson(BleCommunication):
    '''Bluetooth LE communication with Bleson'''

    @staticmethod
    def _run_get_data_background(queue, shared_data, bt_device):
        (observer, q) = BleCommunicationBleson.start(bt_device)

        for advertisement in BleCommunicationBleson.get_lines(q):
            log.debug('Data: %s', advertisement)
            if shared_data['stop']:
                break
            try:
                # macOS doesn't return address on advertised package
                mac = advertisement.address.address if advertisement.address is not None else None
                if mac and mac in shared_data['blacklist']:
                    log.debug('MAC blacklised: %s', mac)
                    continue
                if advertisement.mfg_data is None:
                    continue
                # Linux returns bytearray for mfg_data, but macOS returns _NSInlineData
                # which casts to byte array. We need to explicitly cast it to use hex
                data = bytearray(advertisement.mfg_data) if sys.platform.startswith('darwin') \
                    else advertisement.mfg_data
                # Bleson returns data in a different format than the nix_hci
                # adapter. Since the rest of the processing pipeline is
                # somewhat reliant on the additional data, add to the
                # beginning of the actual data:
                #
                # - An FF type marker
                # - A length marker, covering the vendor specific data
                # - Another length marker, covering the length-marked
                #   vendor data.
                #
                # Thus extended, the result can be parsed by the rest of
                # the pipeline.
                #
                # TODO: This is kinda awkward, and should be handled better.
                data = f'FF{data.hex()}'
                data = f'{(len(data) >> 1):02x}{data}'
                data = f'{(len(data) >> 1):02x}{data}'
                queue.put((mac, data.upper()))
            except GeneratorExit:
                break
            except Exception:
                log.exception('Error in advertisement handling')
                continue

        BleCommunicationBleson.stop(observer)

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
        except KeyboardInterrupt:
            return
        except Exception as ex:
            log.info(ex)
            return

    @staticmethod
    def get_data(blacklist=[], bt_device=''):
        m = Manager()
        q = m.Queue()

        # Use Manager dict to share data between processes
        shared_data = m.dict()
        shared_data['blacklist'] = blacklist
        shared_data['stop'] = False

        # Start background process
        proc = Process(
            target=BleCommunicationBleson._run_get_data_background,
            args=[q, shared_data, bt_device])
        proc.start()

        try:
            while True:
                while not q.empty():
                    data = q.get()
                    yield data
                time.sleep(0.1)
        except GeneratorExit:
            pass

        shared_data['stop'] = True
        proc.join()

    @staticmethod
    def get_first_data(mac, bt_device=''):
        data = None
        data_iter = BleCommunicationBleson.get_data([], bt_device)
        for d in data_iter:
            if mac == d[0]:
                log.info('Data found')
                data_iter.send(StopIteration)
                data = d[1]
                break

        return data
