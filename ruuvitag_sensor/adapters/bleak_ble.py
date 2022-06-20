import asyncio
import logging
from typing import List, Tuple
from bleak import BleakScanner
from bleak.backends.scanner import BLEDevice, AdvertisementData

from ruuvitag_sensor.adapters import BleCommunicationAsync

scanner = BleakScanner()
q = asyncio.Queue[Tuple[str, str]]()

log = logging.getLogger(__name__)


class BleCommunicationBleak(BleCommunicationAsync):

    @staticmethod
    async def _start(queue: asyncio.Queue[Tuple[str, str]], blacklist: List[str]):

        async def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            mac: str = device.address
            if mac and mac in blacklist:
                log.debug('MAC blacklised: %s', mac)
                return

            # Do all RuuviTag's have data in 1177?
            if not 1177 in advertisement_data.manufacturer_data:
                return

            data = advertisement_data.manufacturer_data[1177]
            # Bleak returns data in a different format than the nix_hci
            # adapter. Since the rest of the processing pipeline is
            # somewhat reliant on the additional data, add to the
            # beginning of the actual data:
            #
            # - An FF type marker with 9904 (Ruuvi manufacturer identifer)
            # - A length marker, covering the vendor specific data
            # - Another length marker, covering the length-marked
            #   vendor data.
            #
            # Thus extended, the result can be parsed by the rest of
            # the pipeline.
            #
            # TODO: This is kinda awkward, and should be handled better.
            data = 'FF9904' + data.hex()
            data = '%02x%s' % (len(data) >> 1, data)
            data = '%02x%s' % (len(data) >> 1, data)
            log.info((mac, data))
            await queue.put((mac, data))

        scanner.register_detection_callback(detection_callback)
        await scanner.start()

    @staticmethod
    async def _stop():
        await scanner.stop()

    @staticmethod
    async def get_datas(blacklist: List[str] = [], bt_device: str = '') -> Tuple[str, str]:
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
    async def get_data(mac, bt_device=''):
        pass
