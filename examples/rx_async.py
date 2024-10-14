import asyncio

from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive


async def main():
    ruuvi_rx = RuuviTagReactive()
    subject = ruuvi_rx.get_subject()
    subject.subscribe(print)


if __name__ == "__main__":
    # https://stackoverflow.com/a/56727859/1292530
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
