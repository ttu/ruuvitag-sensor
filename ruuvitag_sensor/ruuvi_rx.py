import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from multiprocessing import Manager
from multiprocessing.managers import DictProxy
from queue import Queue
from threading import Thread

from reactivex import Subject

from ruuvitag_sensor.adapters import is_async_adapter
from ruuvitag_sensor.ruuvi import RunFlag, RuuviTagSensor, ble


async def _run_get_data_background_async(macs: list[str], queue: Queue, shared_data: DictProxy, bt_device: str):
    """
    Async background process function for RuuviTag Sensors
    """
    data_iter = RuuviTagSensor.get_data_async(macs, bt_device)
    try:
        async for data in data_iter:
            if not shared_data["run_flag"]:
                break

            data[1]["time"] = datetime.now(timezone.utc).isoformat()  # type: ignore
            queue.put(data)
    finally:
        await data_iter.aclose()


def _run_get_data_background(macs: list[str], queue: Queue, shared_data: DictProxy, bt_device: str):
    """
    Background process function for RuuviTag Sensors
    """

    run_flag = RunFlag()

    def add_data(data):
        if not shared_data["run_flag"]:
            run_flag.running = False

        data[1]["time"] = datetime.now(timezone.utc).isoformat()
        queue.put(data)

    RuuviTagSensor.get_data(add_data, macs, run_flag, bt_device)


class RuuviTagReactive:
    """
    Reactive wrapper and background process for RuuviTagSensor get_data
    """

    @staticmethod
    def _data_update(subjects: list[Subject], queue: Queue, run_flag: RunFlag):
        """
        Get data from background process and notify all subscribed observers with the new data
        """
        while run_flag.running:
            while not queue.empty():
                data = queue.get()
                for subject in [s for s in subjects if not s.is_disposed]:
                    subject.on_next(data)
            time.sleep(0.1)

    def __init__(self, macs: list[str] | None = None, bt_device: str = ""):
        """
        Start background process for get_data and async task for notifying all subscribed observers

        Args:
            macs (list): MAC addresses
            bt_device (string): Bluetooth device id
        """
        if macs is None:
            macs = []

        self._run_flag = RunFlag()
        self._subjects: list[Subject] = []

        m = Manager()
        q = m.Queue()

        # Use Manager dict to share data between processes
        self._shared_data = m.dict()
        self._shared_data["run_flag"] = True

        # Start data updater

        notify_thread = Thread(target=RuuviTagReactive._data_update, args=(self._subjects, q, self._run_flag))
        notify_thread.start()

        # Start background process

        if is_async_adapter(ble):
            loop = asyncio.get_running_loop()
            loop.create_task(_run_get_data_background_async(macs, q, self._shared_data, bt_device))
        else:
            executor = ProcessPoolExecutor(1)
            executor.submit(_run_get_data_background, macs, q, self._shared_data, bt_device)

    def get_subject(self) -> Subject:
        """
        Returns:
            subject : Reactive Extension Subject
        """

        if not self._run_flag.running:
            raise Exception("RuuviTagReactive stopped")

        subject: Subject = Subject()
        self._subjects.append(subject)
        return subject

    def stop(self):
        """
        Stop get_data
        """

        self._run_flag.running = False
        self._shared_data["run_flag"] = False

        for s in self._subjects:
            s.dispose()
