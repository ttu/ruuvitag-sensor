import asyncio

from ruuvitag_sensor.ruuvi_rx import RuuviTagReactive


async def main():
    ruuvi_rx = RuuviTagReactive()
    subject = ruuvi_rx.get_subject()
    subject.subscribe(print)

    # keep coroutine alive
    try:
        await asyncio.get_running_loop().create_future()
    finally:
        ruuvi_rx.stop()


if __name__ == "__main__":
    asyncio.run(main())
