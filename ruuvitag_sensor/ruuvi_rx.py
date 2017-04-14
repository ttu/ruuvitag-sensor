from datetime import datetime
from multiprocessing import Manager
from threading import Thread
import time
from concurrent.futures import ProcessPoolExecutor
from rx.subjects import Subject

from ruuvitag_sensor.ruuvi import RuuviTagSensor, RunFlag


class RuuviTagReactive(object):
    """
    Reactive wrapper and background process for RuuviTagSensor get_datas
    """

    @staticmethod
    def _run_get_data_background(macs, queue, run_flag):
        """
        Background process from RuuviTag Sensors
        """

        def add_data(data):
            data[1]['time'] = str(datetime.now())
            queue.put(data)

        RuuviTagSensor.get_datas(add_data, macs, run_flag)

    @staticmethod
    def _data_update(subjects, queue, run_flag):
        """
        Get data from backgound process and notify all subscribed observers with the new data
        """
        while run_flag.running:
            while not queue.empty():
                data = queue.get()
                for s in subjects:
                    s.on_next(data)
            time.sleep(0.1)

    def __init__(self, macs=[]):
        """
        Start background process for get_datas and async task for notifying all subscribed observers

        Args:
            macs (list): MAC addresses
        """

        self.subjects = []
        self.run_flag = RunFlag()

        m = Manager()
        q = m.Queue()

        # Start data updater
        notify_thread = Thread(target=RuuviTagReactive._data_update, args=(self.subjects, q, self.run_flag))
        notify_thread.start()

        # Start background process
        executor = ProcessPoolExecutor(1)
        executor.submit(RuuviTagReactive._run_get_data_background, macs, q, self.run_flag)

    def get_subject(self):
        """
        Returns:
            subject : Reactive Extension Subject
        """

        if not self.run_flag.running:
            raise Exception('RuuviTagReactive stopped')

        subject = Subject()
        self.subjects.append(subject)
        return subject

    def stop(self):
        """
        Stop get_datas
        """

        self.run_flag.running = False
        for s in self.subjects:
            s.dispose()
