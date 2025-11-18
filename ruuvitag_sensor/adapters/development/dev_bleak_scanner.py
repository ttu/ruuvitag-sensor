import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from bleak.backends.scanner import AdvertisementData, BLEDevice


@dataclass
class BLEDeviceDummy:
    address: str
    rssi: int


@dataclass
class AdvertisementDataDummy:
    manufacturer_data: dict


data = [
    ("CD:D4:FA:52:7A:F2", -89, b"\x05\x11\xd7E\xd6\xc8\xc2\xff\xfc\x00\x10\x04\x0c\xae\x16\x91{N\xcd\xd4\xfaRz\xf2"),
    ("FE:52:F7:B3:65:CC", -94, b"\x05\x08\xdas\xf0\xc9\r\xff\xc8\xff\xd8\x04\x00\x82\x16\xe0YN\xfeR\xf7\xb3e\xcc"),
    ("EC:4D:A7:95:08:6B", -84, b"\x05\x0c\x99U\x9d\xc9X\x00,\xff\xe8\x04\x10\x83\xd6}\x02F\xecM\xa7\x95\x08k"),
    ("E9:AC:CF:6E:C5:66", -88, b"\x05\x11ZH3\xc8\xc7\x00\x08\x00\x0c\x03\xdc\x83vJj\x94\xe9\xac\xcfn\xc5f"),
]


class DevBleakScanner:
    def __init__(self, callback, _):
        self.callback: Callable[[BLEDevice, AdvertisementData], Awaitable[None]] | None = callback  # type: ignore[annotation-unchecked]
        self.running: bool = False  # type: ignore[annotation-unchecked]

    async def start(self):
        self.running = True
        asyncio.create_task(self.run())

    async def stop(self):
        self.running = False

    async def run(self):
        while self.running:
            selected = random.choice(data)
            device = BLEDeviceDummy(address=selected[0], rssi=selected[1])
            advertisement_data = AdvertisementDataDummy(manufacturer_data={1177: selected[2]})
            if self.callback:
                await self.callback(device, advertisement_data)
            await asyncio.sleep(5)
