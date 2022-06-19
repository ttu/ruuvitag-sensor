import asyncio
import logging
from bleak import BleakScanner
from bleak.backends.scanner import BLEDevice, AdvertisementData

from ruuvitag_sensor.adapters import BleCommunicationAsync

scanner = BleakScanner()
q = asyncio.Queue()

log = logging.getLogger(__name__)


class BleCommunicationBleak(BleCommunicationAsync):

    @staticmethod
    async def _start(queue: asyncio.Queue, blacklist: list[str]):
        '''
        Attributes:
            device (string): BLE device (default 0)
        '''

        async def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            mac = device.address
            if mac and mac in blacklist:
                log.debug('MAC blacklised: %s', mac)
                return
            # TODO: Convert data to a format similar to the rest ruuvi pipeline
            log.info(advertisement_data)
            manufacturer_data = advertisement_data.manufacturer_data[76]
            hex = manufacturer_data.hex()
            await queue.put((mac, hex))

        scanner.register_detection_callback(detection_callback)
        await scanner.start()

    @staticmethod
    async def _stop():
        scanner.stop()

    @staticmethod
    async def get_datas(blacklist: list[str] = [], bt_device: str = ''):
        await BleCommunicationBleak._start(q, blacklist)

        try:
            while True:
                next_item = await q.get()
                mac = next_item[0]
                manufacturer_data = next_item[1]
                yield (mac, manufacturer_data)
        except KeyboardInterrupt as ex:
            pass
        except Exception as ex:
            log.info(ex)

        await BleCommunicationBleak._stop()

    @staticmethod
    async def get_data(mac, bt_device=''):
        pass
