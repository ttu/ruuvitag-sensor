import time
import logging
from queue import Queue
from bleson import get_provider, Observer
from multiprocessing import Manager, Process
from ruuvitag_sensor.adaptors import BleCommunication

log = logging.getLogger(__name__)

class BleCommunicationBleson(BleCommunication):
    '''Bluetooth LE communication with Bleson'''

    @staticmethod
    def _run_get_data_background(queue, shared_data, bt_device):
        (observer, q) = BleCommunicationBleson.start(bt_device)

        for line in BleCommunicationBleson.get_lines(q):
            if shared_data['stop']:
                break
            try:
                mac = line.address.address
                if mac in shared_data['blacklist']:
                    continue
                data = line.service_data or line.mfg_data
                if data is None:
                    continue
                queue.put((mac, data))
            except GeneratorExit:
                break
            except:
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
    def get_datas(blacklist=[], bt_device=''):
        m = Manager()
        q = m.Queue()

        # Use Manager dict to share data between processes
        shared_data = m.dict()
        shared_data['blacklist'] = blacklist
        shared_data['stop'] = False

        # Start background process
        proc = Process(
            target=BleCommunicationBleson._run_get_data_background, 
            args=[q, shared_data, bt_device]
        )
        proc.start()

        try:
            while True:
                while not q.empty():
                    data = q.get()
                    yield data
                log.info("Sleep")
                time.sleep(1)
        except GeneratorExit:
            pass
        except KeyboardInterrupt:
            pass

        shared_data['stop'] = True
        proc.join()
        return

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
