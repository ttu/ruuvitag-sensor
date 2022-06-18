import asyncio
import logging
from bleak import BleakScanner

from ruuvitag_sensor.adapters import BleCommunicationAsync

scanner = BleakScanner()
q = asyncio.Queue()

log = logging.getLogger(__name__)

class BleCommunicationBleak(BleCommunicationAsync):

    @staticmethod
    async def _start(queue: asyncio.Queue, blacklist):
        '''
        Attributes:
            device (string): BLE device (default 0)
        '''
       
        async def detection_callback(device, advertisement_data):
            # TODO: Check blacklist
            await queue.put((device.address, advertisement_data))

        scanner.register_detection_callback(detection_callback)
        await scanner.start()

    @staticmethod
    async def _stop():
        scanner.stop()

    @staticmethod
    async def get_datas(blacklist=[], bt_device=''):
        await BleCommunicationBleak._start(q, blacklist)

        try:
            while True:
                next_item = await q.get()
                yield next_item
        except KeyboardInterrupt as ex:
            pass
        except Exception as ex:
            log.info(ex)

        await BleCommunicationBleak._stop()

    @staticmethod
    def get_data(mac, bt_device=''):
        pass
