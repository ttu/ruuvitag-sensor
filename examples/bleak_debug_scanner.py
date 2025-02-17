"""
Debug scanner that uses Bleak directly to find RuuviTags and print raw BLE advertisement data.

This standalone script bypasses the ruuvitag-sensor library's abstractions to:
1. Help debug BLE connectivity issues
2. Understand raw advertisement data format from RuuviTags
3. Find device-specific UUIDs (especially important on macOS)
4. Test basic Bleak BLE scanning functionality

The script will run indefinitely until interrupted with Ctrl+C.
"""

import asyncio

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

found_tags: dict[str, BLEDevice] = {}


def is_ruuvitag(advertisement_data: AdvertisementData) -> bool:
    """Check if the advertisement data is from a RuuviTag."""
    # RuuviTag manufacturer ID is 0x0499 (1177 in decimal)
    if not advertisement_data.manufacturer_data:
        return False

    return any(company_id == 1177 for company_id in advertisement_data.manufacturer_data)


async def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
    """Callback for when a BLE device is detected."""
    if not is_ruuvitag(advertisement_data):
        return

    if device.address not in found_tags:
        found_tags[device.address] = device
        print(device)
        print(advertisement_data)


async def main():
    scanner = BleakScanner(detection_callback=detection_callback)

    try:
        await scanner.start()
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        await scanner.stop()


if __name__ == "__main__":
    asyncio.run(main())
