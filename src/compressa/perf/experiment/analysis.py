import sqlite3
from typing import Dict, List, Tuple
from datetime import datetime
import statistics
from compressa.perf.db.operations import (
    fetch_measurements_by_experiment,
    fetch_metrics_by_experiment,
    insert_metric,
    insert_parameter
)
from compressa.perf.data.models import (
    Measurement,
    Metric,
    MetricName,
    Parameter,
    Status,
)
from compressa.utils import get_logger

logger = get_logger(__name__)

class Analyzer:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def compute_average_ttft(self, measurements: List[Measurement]) -> float:
        """Average time to first token for successful requests."""
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for TTFT.")
            return 0.0
        
        total_ttft = sum(m.ttft for m in measurements)
        return total_ttft / len(measurements)

    def compute_q95_ttft(self, measurements: List[Measurement]) -> float:
        """95th percentile time to first token for successful requests."""
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for 95th percentile TTFT.")
            return 0.0
        ttfts = sorted(m.ttft for m in measurements)
        n = len(ttfts)
        index = 0.95 * (n - 1)
        lower = int(index)
        upper = lower + 1
        if upper >= n:
            return ttfts[lower]
        return ttfts[lower] + (ttfts[upper] - ttfts[lower]) * (index - lower)

    def compute_top_5_ttft(self, measurements: List[Measurement]) -> float:
        """
        Average TTFT of the slowest 5% of successful requests.
        If fewer than 20 successful measurements exist, the top 5%
        may be 1 request or none if the slice is empty—handle that edge.
        """
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for top 5% TTFT.")
            return 0.0
        
        ttfts = sorted(m.ttft for m in measurements)
        n = len(ttfts)
        cutoff_index = int(0.95 * n)  # start of the top 5% slice
        if cutoff_index >= n:
            # Edge case: if n=1, .95*(n-1) might be 0. 
            # but usually you'd see at least 1 item anyway
            return 0.0
        
        top_5_ttfts = ttfts[cutoff_index:]
        return sum(top_5_ttfts) / len(top_5_ttfts)

    def compute_average_latency(self, measurements: List[Measurement]) -> float:
        """Average latency for successful requests."""
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for average latency.")
            return 0.0
        total_latency = sum((m.end_time - m.start_time) for m in measurements)
        return total_latency / len(measurements)

    def compute_q95_latency(self, measurements: List[Measurement]) -> float:
        """95th percentile latency for successful requests."""
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for 95th percentile latency.")
            return 0.0
        latencies = sorted((m.end_time - m.start_time) for m in measurements)
        n = len(latencies)
        index = 0.95 * (n - 1)
        lower = int(index)
        upper = lower + 1
        if upper >= n:
            return latencies[lower]
        return latencies[lower] + (latencies[upper] - latencies[lower]) * (index - lower)

    def compute_top_5_latency(self, measurements: List[Measurement]) -> float:
        """
        Average latency of the slowest 5% of successful requests.
        """
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for top 5% latency.")
            return 0.0
        latencies = sorted((m.end_time - m.start_time) for m in measurements)
        n = len(latencies)
        cutoff_index = int(0.95 * n)
        if cutoff_index >= n:
            return 0.0
        top_5_latencies = latencies[cutoff_index:]
        return sum(top_5_latencies) / len(top_5_latencies)

    def compute_average_time_per_output_token(self, measurements: List[Measurement]) -> float:
        """Average total latency per output token for successful requests."""
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for time per output token.")
            return 0.0
        total_latency = sum((m.end_time - m.start_time) for m in measurements)
        total_output_tokens = sum(m.n_output for m in measurements)
        return total_latency / total_output_tokens if total_output_tokens > 0 else 0.0

    def compute_throughput(self, measurements: List[Measurement]) -> float:
        """
        Tokens (input + output) per second across all successful requests,
        measured from the earliest start_time to the latest end_time.
        """
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for throughput.")
            return 0.0
        total_input_tokens = sum(m.n_input for m in measurements)
        total_output_tokens = sum(m.n_output for m in measurements)
        total_tokens = total_input_tokens + total_output_tokens
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time = experiment_end_time - experiment_start_time
        return total_tokens / total_time if total_time > 0 else 0.0

    def compute_throughput_input_tokens(self, measurements: List[Measurement]) -> float:
        """Input tokens per second for successful requests."""
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for throughput input tokens.")
            return 0.0
        total_input_tokens = sum(m.n_input for m in measurements)
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time = experiment_end_time - experiment_start_time
        return total_input_tokens / total_time if total_time > 0 else 0.0

    def compute_throughput_output_tokens(self, measurements: List[Measurement]) -> float:
        """Output tokens per second for successful requests."""
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for throughput output tokens.")
            return 0.0
        total_output_tokens = sum(m.n_output for m in measurements)
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time = experiment_end_time - experiment_start_time
        return total_output_tokens / total_time if total_time > 0 else 0.0

    def compute_input_output_stats(self, measurements: List[Measurement]) -> Dict[str, float]:
        """
        Basic stats on the number of input/output tokens for successful requests.
        """
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for input/output stats.")
            return {
                "avg_n_input": 0.0,
                "std_n_input": 0.0,
                "avg_n_output": 0.0,
                "std_n_output": 0.0
            }
        n_inputs = [m.n_input for m in measurements]
        n_outputs = [m.n_output for m in measurements]
        
        return {
            "avg_n_input": statistics.mean(n_inputs),
            "std_n_input": statistics.stdev(n_inputs) if len(n_inputs) > 1 else 0.0,
            "avg_n_output": statistics.mean(n_outputs),
            "std_n_output": statistics.stdev(n_outputs) if len(n_outputs) > 1 else 0.0
        }

    def compute_rps(self, measurements: List[Measurement]) -> float:
        """
        Requests per second (RPS) for successful requests:
        number of successful requests / (max(end_time) - min(start_time)).
        """
        measurements = [m for m in measurements if m.status == Status.SUCCESS]
        if not measurements:
            logger.warning("No successful measurements found for RPS.")
            return 0.0
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time = experiment_end_time - experiment_start_time
        return len(measurements) / total_time if total_time > 0 else 0.0

    def compute_longer_than_60_latency(self, measurements: List[Measurement]) -> int:
        """
        Count how many successful requests took more than 60 seconds.
        """
        successes = [m for m in measurements if m.status == Status.SUCCESS]
        if not successes:
            return 0
        return sum(1 for m in successes if (m.end_time - m.start_time) > 60)

    def compute_longer_than_120_latency(self, measurements: List[Measurement]) -> int:
        """
        Count how many successful requests took more than 120 seconds.
        """
        successes = [m for m in measurements if m.status == Status.SUCCESS]
        return sum(1 for m in successes if (m.end_time - m.start_time) > 120)

    def compute_longer_than_180_latency(self, measurements: List[Measurement]) -> int:
        """
        Count how many successful requests took more than 180 seconds.
        """
        successes = [m for m in measurements if m.status == Status.SUCCESS]
        return sum(1 for m in successes if (m.end_time - m.start_time) > 180)

    def compute_failed_requests(self, measurements: List[Measurement]) -> int:
        """
        Count total failed requests (status == FAILURE).
        """
        return sum(1 for m in measurements if m.status == Status.FAILED)

    def compute_failed_requests_per_hour(self, measurements: List[Measurement]) -> float:
        """
        Number of failed requests per hour = (total failed / total experiment time in hours).
        """
        if not measurements:
            return 0.0

        failed_count = sum(1 for m in measurements if m.status == Status.FAILED)
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time_seconds = experiment_end_time - experiment_start_time

        if total_time_seconds <= 0:
            return 0.0

        total_time_hours = total_time_seconds / 3600.0
        return failed_count / total_time_hours


    def compute_metrics(self, experiment_id: int):
        measurements = fetch_measurements_by_experiment(self.conn, experiment_id)
        if not measurements:
            raise ValueError(f"No measurements found for experiment_id {experiment_id}")

        metrics_dict, io_stats = self.compute_metrics_for_measurements(measurements)
        if not metrics_dict:
            raise ValueError(f"No successful measurements found for experiment_id {experiment_id}")

        from datetime import datetime
        now = datetime.now()
        for base_name, val in metrics_dict.items():
            metric = Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=base_name,
                metric_value=val,
                timestamp=now
            )
            insert_metric(metric)
            # self.conn.commit()

        for key, value in io_stats.items():
            param = Parameter(
                id=None,
                experiment_id=experiment_id,
                key=key,
                value=str(value)
            )
            insert_parameter(param)
            # self.conn.commit()

        return metrics_dict, io_stats

    def compute_metrics_for_measurements(
        self,
        measurements: List[Measurement]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Compute the standard set of metrics on a given subset of measurements.
        Returns:
          (metrics_dict, io_stats)
            metrics_dict: { base_metric_name -> value, ... }
            io_stats: { "avg_n_input" -> val, "std_n_input" -> val, ... }
        If no measurements exist or all are invalid, returns two empty dicts.
        """
        if not measurements:
            return {}, {}

        average_ttft = self.compute_average_ttft(measurements)
        q95_ttft = self.compute_q95_ttft(measurements)
        top_5_ttft = self.compute_top_5_ttft(measurements)

        average_latency = self.compute_average_latency(measurements)
        q95_latency = self.compute_q95_latency(measurements)
        top_5_latency = self.compute_top_5_latency(measurements)

        average_time_per_output_token = self.compute_average_time_per_output_token(measurements)
        throughput = self.compute_throughput(measurements)
        throughput_input_tokens = self.compute_throughput_input_tokens(measurements)
        throughput_output_tokens = self.compute_throughput_output_tokens(measurements)
        rps = self.compute_rps(measurements)

        longer_than_60_latency = self.compute_longer_than_60_latency(measurements)
        longer_than_120_latency = self.compute_longer_than_120_latency(measurements)
        longer_than_180_latency = self.compute_longer_than_180_latency(measurements)
        failed_requests = self.compute_failed_requests(measurements)
        failed_requests_per_hour = self.compute_failed_requests_per_hour(measurements)

        io_stats = self.compute_input_output_stats(measurements)

        metrics_dict = {
            MetricName.TTFT.value: average_ttft,
            MetricName.TTFT_95.value: q95_ttft,
            MetricName.TOP_5_TTFT.value: top_5_ttft,
            MetricName.LATENCY.value: average_latency,
            MetricName.LATENCY_95.value: q95_latency,
            MetricName.TOP_5_LATENCY.value: top_5_latency,
            MetricName.TPOT.value: average_time_per_output_token,
            MetricName.THROUGHPUT.value: throughput,
            MetricName.THROUGHPUT_INPUT_TOKENS.value: throughput_input_tokens,
            MetricName.THROUGHPUT_OUTPUT_TOKENS.value: throughput_output_tokens,
            MetricName.RPS.value: rps,
            MetricName.LONGER_THAN_60_LATENCY.value: longer_than_60_latency,
            MetricName.LONGER_THAN_120_LATENCY.value: longer_than_120_latency,
            MetricName.LONGER_THAN_180_LATENCY.value: longer_than_180_latency,
            MetricName.FAILED_REQUESTS.value: failed_requests,
            MetricName.FAILED_REQUESTS_PER_HOUR.value: failed_requests_per_hour,
        }

        return metrics_dict, io_stats