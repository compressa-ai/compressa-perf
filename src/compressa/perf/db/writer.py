import sqlite3
import queue
import threading
from dataclasses import dataclass
from typing import Any, Optional
from compressa.perf.db.db_inserts import (
    direct_insert_measurement,
    direct_insert_metric,
    direct_insert_parameter,
)
from compressa.perf.data.models import Measurement, Metric, Parameter

class WriteItemType:
    MEASUREMENT = "measurement"
    METRIC = "metric"
    PARAMETER = "parameter"

@dataclass
class DBWriteItem:
    item_type: str
    item_data: Any

class DBWriterThread:
    def __init__(self, db_path: str, batch_size: int = 2):
        self.db_path = db_path
        self.batch_size = batch_size
        self.queue = queue.Queue()
        self.running = True
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        conn = sqlite3.connect(self.db_path)
        items_batch = []

        def flush_batch():
            if not items_batch:
                return
            with conn:
                for it in items_batch:
                    self._insert(conn, it)
                    # conn.commit()
            for _ in items_batch:
                self.queue.task_done()
            items_batch.clear()

        while self.running:
            try:
                item = self.queue.get(timeout=0.1)
            except queue.Empty:
                flush_batch()
                continue

            if item is None:
                flush_batch()
                break

            items_batch.append(item)

            if len(items_batch) >= self.batch_size:
                flush_batch()

        flush_batch()
        conn.close()

    def _insert(self, conn, item: DBWriteItem):
        if item.item_type == WriteItemType.MEASUREMENT:
            direct_insert_measurement(conn, item.item_data)
        elif item.item_type == WriteItemType.METRIC:
            direct_insert_metric(conn, item.item_data)
        elif item.item_type == WriteItemType.PARAMETER:
            direct_insert_parameter(conn, item.item_data)

    def stop(self):
        self.running = False
        self.queue.put(None)
        self.wait_for_write()
        if self.thread:
            self.thread.join()

    def push_measurement(self, measurement: Measurement):
        self.queue.put(DBWriteItem(WriteItemType.MEASUREMENT, measurement))

    def push_metric(self, metric: Metric):
        self.queue.put(DBWriteItem(WriteItemType.METRIC, metric))

    def push_parameter(self, parameter: Parameter):
        self.queue.put(DBWriteItem(WriteItemType.PARAMETER, parameter))

    def wait_for_write(self, timeout: float = 10.0) -> bool:
        e = threading.Event()

        def run_join():
            self.queue.join()
            e.set()

        t = threading.Thread(target=run_join, daemon=True)
        t.start()
        t.join(timeout=timeout)
        return e.is_set()
