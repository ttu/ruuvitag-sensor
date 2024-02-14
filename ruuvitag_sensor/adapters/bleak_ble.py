import asyncio
import logging
import os
import re
import sys
from typing import AsyncGenerator, List, Tuple

from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData, AdvertisementDataCallback, BLEDevice

from ruuvitag_sensor.adapters import BleCommunicationAsync
from ruuvitag_sensor.adapters.utils import rssi_to_hex
from ruuvitag_sensor.ruuvi_types import MacAndRawData, RawData

MAC_REGEX = "[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$"


def _get_scanner(detection_callback: AdvertisementDataCallback, bt_device: str = ""):
    # NOTE: On Linux - bleak.exc.BleakError: passive scanning mode requires bluez or_patterns
    # NOTE: On macOS - bleak.exc.BleakError: macOS does not support passive scanning
    scanning_mode = "passive" if sys.platform.startswith("win") else "active"

    if "bleak_dev" in os.environ.get("RUUVI_BLE_ADAPTER", "").lower():
        # pylint: disable=import-outside-toplevel
        from ruuvitag_sensor.adapters.development.dev_bleak_scanner import DevBleakScanner

        return DevBleakScanner(detection_callback, scanning_mode)

    if bt_device:
        return BleakScanner(
            detection_callback=detection_callback, scanning_mode=scanning_mode, adapter=bt_device
        )  # type: ignore[arg-type]

    return BleakScanner(detection_callback=detection_callback, scanning_mode=scanning_mode)  # type: ignore[arg-type]


# TODO: Python 3.7 - TypeError: 'type' object is not subscriptable
# queue = asyncio.Queue[Tuple[str, str]]()
queue = asyncio.Queue()  # type: ignore

log = logging.getLogger(__name__)


class BleCommunicationBleak(BleCommunicationAsync):
    @staticmethod
    def _parse_data(data: bytes) -> str:
        # Bleak returns data in a different format than the nix_hci
        # adapter. Since the rest of the processing pipeline is
        # somewhat reliant on the additional data, add to the
        # beginning of the actual data:
        #
        # - An FF type marker with 9904 (Ruuvi manufacturer identifier)
        # - A length marker, covering the vendor specific data
        # - Another length marker, covering the length-marked
        #   vendor data.
        #
        # Thus extended, the result can be parsed by the rest of
        # the pipeline.
        #
        # TODO: This is kinda awkward, and should be handled better.
        formatted = f"FF9904{data.hex()}"
        formatted = f"{(len(formatted) >> 1):02x}{formatted}"
        formatted = f"{(len(formatted) >> 1):02x}{formatted}"
        return formatted

    @staticmethod
    async def get_data(blacklist: List[str] = [], bt_device: str = "") -> AsyncGenerator[MacAndRawData, None]:
        async def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
            # On macOS device address is not a MAC address, but a system specific ID
            # https://github.com/hbldh/bleak/issues/140
            mac: str = device.address if re.match(MAC_REGEX, device.address.lower()) else ""
            if mac and mac in blacklist:
                log.debug("MAC blacklised: %s", mac)
                return

            # TODO: Do all RuuviTags have data in 1177?
            if 1177 not in advertisement_data.manufacturer_data:
                return

            log.debug("Received data: %s", advertisement_data)

            data = BleCommunicationBleak._parse_data(advertisement_data.manufacturer_data[1177])

            # Add RSSI to encoded data as hex. All adapters use a common decoder.
            data += rssi_to_hex(advertisement_data.rssi)
            await queue.put((mac, data))

        scanner = _get_scanner(detection_callback, bt_device)
        await scanner.start()

        log.debug("Bleak scanner started")

        try:
            while True:
                next_item: Tuple[str, str] = await queue.get()
                yield next_item
        except KeyboardInterrupt:
            pass
        except GeneratorExit:
            pass
        except Exception as ex:
            log.info(ex)

        await scanner.stop()

        log.debug("Bleak scanner stopped")

    @staticmethod
    async def get_first_data(mac: str, bt_device: str = "") -> RawData:
        """
        NOTE: get_first_data does not work on macOS.

        macOS doesn't return MAC address, as it uses system specific IDs
        """
        data = None
        data_iter = BleCommunicationBleak.get_data([], bt_device)
        async for d in data_iter:
            if mac == d[0]:
                log.info("Data found")
                data = d[1]
                await data_iter.aclose()

        return data or ""
