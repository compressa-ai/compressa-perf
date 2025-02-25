# File: compressa/perf/experiment/continuous_stress.py

import time
import threading
import random
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import List
from datetime import datetime

from compressa.perf.experiment.inference import InferenceRunner
from compressa.perf.experiment.analysis import Analyzer
from compressa.perf.data.models import (
    Measurement,
    Metric,
    Parameter,
    Status,
    MetricName,
)
from compressa.perf.db.operations import insert_measurement, insert_parameter, insert_metric
from compressa.utils import get_logger

logger = get_logger(__name__)


class ContinuousStressTestRunner:
    """
    Runs inference requests continuously. Every 'report_freq_min' minutes,
    it computes metrics on the last window of measurements and stores them
    in DB with a suffix like "ttft_window_1", etc. Also prints them in real-time.
    """

    def __init__(
        self,
        db_path: str,
        api_key: str,
        openai_url: str,
        model_name: str,
        experiment_id: int,
        prompts: List[str],
        num_runners: int,
        max_tokens: int,
        report_freq_min: float,
        seed: int = 42,
    ):
        self.db_path = db_path
        self.api_key = api_key
        self.openai_url = openai_url
        self.model_name = model_name
        self.experiment_id = experiment_id
        self.prompts = prompts
        self.num_runners = num_runners
        self.max_tokens = max_tokens
        self.report_freq_sec = report_freq_min * 60
        self.running = True

        self.experiment_start_ts = time.time()
        self.window_count = 1

        self.choise_generator = random.Random(seed)

    def start_test(self):
        """
        Launches two threads:
          1) A worker thread (or pool) sending requests continuously
          2) A metrics thread computing windowed metrics every report_freq_sec
        """
        self.executor = ThreadPoolExecutor(max_workers=self.num_runners)
        self.inference_runner = InferenceRunner(
            api_key=self.api_key,
            openai_url=self.openai_url,
            model_name=self.model_name,
        )

        self._store_continuous_params()

        t_infer = threading.Thread(
            target=self._continuous_inference_loop,
            daemon=True,
        )
        t_infer.start()

        t_metrics = threading.Thread(
            target=self._metrics_loop,
            daemon=True,
        )
        t_metrics.start()

        logger.info("Continuous stress test started. Press Ctrl+C to stop.")

        # Keep main thread alive until user stops
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping continuous stress test.")
            self.running = False
            self.executor.shutdown(wait=False)

    def _continuous_inference_loop(self):
        """
        Continuously schedule inference tasks in the thread pool.
        """
        while self.running:
            prompt = self.choise_generator.choice(self.prompts)
            self.executor.submit(self._do_inference_task, prompt)
            # Short pause to avoid spamming the server too rapidly
            time.sleep(0.01)

    def _do_inference_task(self, prompt: str):
        """
        Single inference call. Stores the resulting measurement to DB.
        """
        meas: Measurement = self.inference_runner.run_inference(
            experiment_id=self.experiment_id,
            prompt=prompt,
            max_tokens=self.max_tokens,
        )
        insert_measurement(meas)

    def _metrics_loop(self):
        """
        Every 'report_freq_sec', compute metrics for the time window
        [start, end], store them in the DB (with a suffix), and log them.
        """
        

        while self.running:
            time.sleep(self.report_freq_sec)

            window_start = self.experiment_start_ts
            window_end = self.experiment_start_ts + self.window_count * self.report_freq_sec

            with sqlite3.connect(self.db_path) as conn:
                analyzer = Analyzer(conn)
                self._compute_and_store_window_metrics(
                    conn,
                    analyzer,
                    window_start,
                    window_end,
                    self.window_count,
                )
                self.window_count += 1

    def _compute_and_store_window_metrics(
        self,
        conn: sqlite3.Connection,
        analyzer: Analyzer,
        start_ts: float,
        end_ts: float,
        window_index: int,
    ):
        """
        Fetch measurements in [start_ts, end_ts], compute standard metrics via Analyzer,
        then store them with a suffix. Also logs them in real time.
        """
        cursor = conn.cursor()
        sql = """
            SELECT * FROM Measurements
             WHERE experiment_id = ?
               AND start_time >= ?
               AND end_time <= ?
        """
        cursor.execute(sql, (self.experiment_id, start_ts, end_ts))
        rows = cursor.fetchall()
        measurements = []
        for row in rows:
            measurements.append(
                Measurement(
                    id=row[0],
                    experiment_id=row[1],
                    n_input=row[2],
                    n_output=row[3],
                    ttft=row[4],
                    start_time=row[5],
                    end_time=row[6],
                    status=Status(row[7]),
                )
            )

        if not measurements:
            logger.info(f"No measurements found in window {window_index} ({int(start_ts)}-{int(end_ts)}).")
            return

        metrics_dict, io_stats = analyzer.compute_metrics_for_measurements(measurements)
        if not metrics_dict:
            logger.info(f"No valid metrics in window {window_index}. Possibly all failed.")
            return

        now = datetime.now()

        for base_name, value in metrics_dict.items():
            metric_name = f"{base_name}_window_{window_index}"
            metric = Metric(
                id=None,
                experiment_id=self.experiment_id,
                metric_name=metric_name,
                metric_value=value,
                timestamp=now
            )
            insert_metric(metric)

        for io_key, io_val in io_stats.items():
            param_name = f"{io_key}_window_{window_index}"
            param = Parameter(
                id=None,
                experiment_id=self.experiment_id,
                key=param_name,
                value=str(io_val)
            )
            insert_parameter(param)

        avg_ttft = metrics_dict.get(MetricName.TTFT.value, 0.0)
        avg_lat = metrics_dict.get(MetricName.LATENCY.value, 0.0)
        rps = metrics_dict.get(MetricName.RPS.value, 0.0)
        fails = metrics_dict.get(MetricName.FAILED_REQUESTS.value, 0.0)
        logger.info(f"[Window {window_index}] TTFT={avg_ttft:.3f}s, LAT={avg_lat:.3f}s, RPS={rps:.3f}, FAILS={fails}")

    def _store_continuous_params(self):
        """
        Store some parameters about the continuous run using the Parameter dataclass.
        """
        param_list = [
            ("run_mode", "continuous"),
            ("num_workers", str(self.num_runners)),
            ("max_tokens", str(self.max_tokens)),
            ("report_freq_min", str(int(self.report_freq_sec // 60))),
            ("model_name", self.model_name),
            ("openai_url", self.openai_url),
        ]
        for k, v in param_list:
            p = Parameter(
                id=None,
                experiment_id=self.experiment_id,
                key=k,
                value=v
            )
            insert_parameter(p)
