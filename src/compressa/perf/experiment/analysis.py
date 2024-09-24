import sqlite3
from typing import Dict, List
from compressa.perf.db.operations import fetch_measurements_by_experiment
from compressa.perf.data.models import Measurement

class Analyzer:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def compute_average_ttft(self, measurements: List[Measurement]) -> float:
        total_ttft = sum(m.ttft for m in measurements)
        return total_ttft / len(measurements)

    def compute_average_latency(self, measurements: List[Measurement]) -> float:
        total_latency = sum((m.end_time - m.start_time) for m in measurements)
        return total_latency / len(measurements)

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

    def compute_metrics(self, experiment_id: int) -> Dict[str, float]:
        measurements = fetch_measurements_by_experiment(self.conn, experiment_id)
        
        if not measurements:
            raise ValueError(f"No measurements found for experiment_id {experiment_id}")

        average_ttft = self.compute_average_ttft(measurements)
        average_latency = self.compute_average_latency(measurements)
        average_time_per_output_token = self.compute_average_time_per_output_token(measurements)
        throughput = self.compute_throughput(measurements)

        return {
            "average_ttft": average_ttft,
            "average_latency": average_latency,
            "average_time_per_output_token": average_time_per_output_token,
            "throughput": throughput,
        }
