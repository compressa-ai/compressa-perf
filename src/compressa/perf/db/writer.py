# File: compressa/perf/db/db_writer.py

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

from compressa.perf.data.models import (
    Measurement,
    Metric,
    Parameter,
)


class WriteItemType:
    MEASUREMENT = "measurement"
    METRIC = "metric"
    PARAMETER = "parameter"


@dataclass
class DBWriteItem:
    item_type: str
    item_data: Any


class DBWriterThread:
    """
    A single background thread that:
      - holds the sqlite3.Connection
      - reads DBWriteItem objects from a queue
      - calls insert_* functions
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.queue = queue.Queue()
        self.running = True
        self.thread: Optional[threading.Thread] = None

    def start(self):
        """Starts the writer in a daemon thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        """Main loop: open the DB connection, process queue items, stop when None is received."""
        conn = sqlite3.connect(self.db_path)
        while self.running:
            item = self.queue.get()
            if item is None:
                break  # sentinel => stop
            if not isinstance(item, DBWriteItem):
                self.queue.task_done()
                continue

            with conn:
                if item.item_type == WriteItemType.MEASUREMENT:
                    direct_insert_measurement(conn, item.item_data)
                elif item.item_type == WriteItemType.METRIC:
                    direct_insert_metric(conn, item.item_data)
                elif item.item_type == WriteItemType.PARAMETER:
                    direct_insert_parameter(conn, item.item_data)

            self.queue.task_done()

        conn.close()

    def stop(self):
        """Send stop signal and wait for the thread to join."""
        self.running = False
        self.queue.put(None)  # sentinel
        if self.thread:
            self.thread.join()

    def push_measurement(self, measurement: Measurement):
        self.queue.put(DBWriteItem(WriteItemType.MEASUREMENT, measurement))

    def push_metric(self, metric: Metric):
        self.queue.put(DBWriteItem(WriteItemType.METRIC, metric))

    def push_parameter(self, parameter: Parameter):
        self.queue.put(DBWriteItem(WriteItemType.PARAMETER, parameter))
