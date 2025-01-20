import sqlite3
from typing import Dict, List
from datetime import datetime
import statistics
from compressa.perf.db.operations import (
    fetch_measurements_by_experiment,
    insert_metric,
    insert_parameter
)
from compressa.perf.data.models import (
    Measurement,
    Metric,
    MetricName,
    Parameter
)

class Analyzer:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def compute_average_ttft(self, measurements: List[Measurement]) -> float:
        total_ttft = sum(m.ttft for m in measurements)
        return total_ttft / len(measurements)

    def compute_q95_ttft(self, measurements: List[Measurement]) -> float:
        ttfts = sorted(m.ttft for m in measurements)
        n = len(ttfts)
        if n == 0:
            return 0    
        index = 0.95 * (n - 1)
        lower = int(index)
        upper = lower + 1
        if upper >= n:
            return ttfts[lower]
        return ttfts[lower] + (ttfts[upper] - ttfts[lower]) * (index - lower)

    def compute_average_latency(self, measurements: List[Measurement]) -> float:
        total_latency = sum((m.end_time - m.start_time) for m in measurements)
        return total_latency / len(measurements)

    def compute_q95_latency(self, measurements: List[Measurement]) -> float:
        latencies = sorted((m.end_time - m.start_time) for m in measurements)
        n = len(latencies)
        if n == 0:
            return 0
        index = 0.95 * (n - 1)
        lower = int(index)
        upper = lower + 1
        if upper >= n:
            return latencies[lower]
        return latencies[lower] + (latencies[upper] - latencies[lower]) * (index - lower)

    def compute_average_time_per_output_token(self, measurements: List[Measurement]) -> float:
        total_latency = sum((m.end_time - m.start_time) for m in measurements)
        total_output_tokens = sum(m.n_output for m in measurements)
        return total_latency / total_output_tokens if total_output_tokens > 0 else 0

    def compute_throughput(self, measurements: List[Measurement]) -> float:
        total_input_tokens = sum(m.n_input for m in measurements)
        total_output_tokens = sum(m.n_output for m in measurements)
        total_tokens = total_input_tokens + total_output_tokens
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time = experiment_end_time - experiment_start_time
        return total_tokens / total_time if total_time > 0 else 0

    def compute_throughput_input_tokens(self, measurements: List[Measurement]) -> float:
        total_input_tokens = sum(m.n_input for m in measurements)
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time = experiment_end_time - experiment_start_time
        return total_input_tokens / total_time if total_time > 0 else 0

    def compute_throughput_output_tokens(self, measurements: List[Measurement]) -> float:
        total_output_tokens = sum(m.n_output for m in measurements)
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time = experiment_end_time - experiment_start_time
        return total_output_tokens / total_time if total_time > 0 else 0

    def compute_input_output_stats(self, measurements: List[Measurement]) -> Dict[str, float]:
        n_inputs = [m.n_input for m in measurements]
        n_outputs = [m.n_output for m in measurements]
        
        return {
            "avg_n_input": statistics.mean(n_inputs),
            "std_n_input": statistics.stdev(n_inputs),
            "avg_n_output": statistics.mean(n_outputs),
            "std_n_output": statistics.stdev(n_outputs)
        }

    def compute_rps(self, measurements: List[Measurement]) -> float:
        experiment_start_time = min(m.start_time for m in measurements)
        experiment_end_time = max(m.end_time for m in measurements)
        total_time = experiment_end_time - experiment_start_time
        return len(measurements) / total_time if total_time > 0 else 0

    def compute_metrics(self, experiment_id: int):
        measurements = fetch_measurements_by_experiment(self.conn, experiment_id)
        
        if not measurements:
            raise ValueError(f"No measurements found for experiment_id {experiment_id}")

        average_ttft = self.compute_average_ttft(measurements)
        average_latency = self.compute_average_latency(measurements)
        q95_ttft = self.compute_q95_ttft(measurements)
        q95_latency = self.compute_q95_latency(measurements)
        average_time_per_output_token = self.compute_average_time_per_output_token(measurements)
        throughput = self.compute_throughput(measurements)
        throughput_input_tokens = self.compute_throughput_input_tokens(measurements)
        throughput_output_tokens = self.compute_throughput_output_tokens(measurements)
        input_output_stats = self.compute_input_output_stats(measurements)
        rps = self.compute_rps(measurements)
        
        metrics = [
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.TTFT,
                metric_value=average_ttft,
                timestamp=datetime.now()
            ),
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.TTFT_95,
                metric_value=q95_ttft,
                timestamp=datetime.now()
            ),
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.LATENCY,
                metric_value=average_latency,
                timestamp=datetime.now()
            ),
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.LATENCY_95,
                metric_value=q95_latency,
                timestamp=datetime.now()
            ),
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.TPOT,
                metric_value=average_time_per_output_token,
                timestamp=datetime.now()
            ),
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.THROUGHPUT,
                metric_value=throughput,
                timestamp=datetime.now()
            ),
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.THROUGHPUT_INPUT_TOKENS,
                metric_value=throughput_input_tokens,
                timestamp=datetime.now()
            ),
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.THROUGHPUT_OUTPUT_TOKENS,
                metric_value=throughput_output_tokens,
                timestamp=datetime.now()
            ),
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.RPS,
                metric_value=rps,
                timestamp=datetime.now()
            )
        ]

        for metric in metrics:
            insert_metric(self.conn, metric)

        for key, value in input_output_stats.items():
            parameter = Parameter(
                id=None,
                experiment_id=experiment_id,
                key=key,
                value=str(value)
            )
            insert_parameter(self.conn, parameter)
