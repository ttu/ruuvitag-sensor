import time
from threading import Thread
from datetime import datetime
from multiprocessing import Manager
from concurrent.futures import ProcessPoolExecutor
from rx.subjects import Subject
from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag


def _run_get_data_background(macs, queue, shared_data, bt_device):
    """
    Background process function for RuuviTag Sensors
    """

    run_flag = RunFlag()

    def add_data(data):
        if not shared_data['run_flag']:
            run_flag.running = False

        data[1]['time'] = datetime.utcnow().isoformat()
        queue.put(data)

    RuuviTagSensor.get_datas(add_data, macs, run_flag, bt_device)


class RuuviTagReactive(object):
    """
    Reactive wrapper and background process for RuuviTagSensor
    get_datas
    """

    @staticmethod
    def _data_update(subjects, queue, run_flag):
        """
        Get data from backgound process and notify all subscribed observers
        with the new data
        """
        while run_flag.running:
            while not queue.empty():
                data = queue.get()
                for subject in [s for s in subjects if not s.is_disposed]:
                    subject.on_next(data)
            time.sleep(0.1)

    def __init__(self, macs=[], bt_device=''):
        """
        Start background process for get_datas and async task for notifying
        all subscribed observers

        Args:
            macs (list): MAC addresses
            bt_device (string): Bluetooth device id
        """

        self._run_flag = RunFlag()
        self._subjects = []

        m = Manager()
        q = m.Queue()

        # Use Manager dict to share data between processes
        self._shared_data = m.dict()
        self._shared_data['run_flag'] = True

        # Start data updater
        notify_thread = Thread(
            target=RuuviTagReactive._data_update,
            args=(self._subjects, q, self._run_flag))
        notify_thread.start()

        # Start background process
        executor = ProcessPoolExecutor(1)
        executor.submit(
            _run_get_data_background,
            macs, q, self._shared_data, bt_device)

    def get_subject(self):
        """
        Returns:
            subject : Reactive Extension Subject
        """

        if not self._run_flag.running:
            raise Exception('RuuviTagReactive stopped')

        subject = Subject()
        self._subjects.append(subject)
        return subject

    def stop(self):
        """
        Stop get_datas
        """

        self._run_flag.running = False
        self._shared_data['run_flag'] = False

        for s in self._subjects:
            s.dispose()
