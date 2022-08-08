import asyncio
import logging
import sys
from typing import List, Tuple
from bleak import BleakScanner
from bleak.backends.scanner import BLEDevice, AdvertisementData

from ruuvitag_sensor.adapters import BleCommunicationAsync

# NOTE: On Linux - bleak.exc.BleakError: passive scanning mode requires bluez or_patterns
scanning_mode = "active" if sys.platform.startswith('linux') else "passive"
scanner = BleakScanner(scanning_mode=scanning_mode)

# TODO: Python 3.7 - TypeError: 'type' object is not subscriptable
# queue = asyncio.Queue[Tuple[str, str]]()
queue = asyncio.Queue()

log = logging.getLogger(__name__)


class BleCommunicationBleak(BleCommunicationAsync):

    @staticmethod
    def _parse_data(data: bytes) -> str:
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
        return data

    @staticmethod
    async def _stop():
        await scanner.stop()

    @staticmethod
    async def get_data(blacklist: List[str] = [], bt_device: str = '') -> Tuple[str, str]:
        async def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            mac: str = device.address
            if mac and mac in blacklist:
                log.debug('MAC blacklised: %s', mac)
                return

            # TODO: Do all RuuviTags have data in 1177?
            if 1177 not in advertisement_data.manufacturer_data:
                return

            data = BleCommunicationBleak._parse_data(advertisement_data.manufacturer_data[1177])
            
            # Add RSSI to encoded data as hex. All adapters use a common decoder.
            data += hex((device.rssi + (1 << 8)) % (1 << 8)).replace('0x', '')
            
            await queue.put((mac, data))

        scanner.register_detection_callback(detection_callback)
        await scanner.start()

        try:
            while True:
                next_item = await queue.get()
                yield next_item
        except KeyboardInterrupt:
            pass
        except GeneratorExit:
            pass
        except Exception as ex:
            log.info(ex)

        await BleCommunicationBleak._stop()

    @staticmethod
    async def get_first_data(mac, bt_device=''):
        data = None
        data_iter = BleCommunicationBleak.get_data([], bt_device)
        async for d in data_iter:
            if mac == d[0]:
                log.info('Data found')
                data = d[1]
                await data_iter.aclose()

        return data
