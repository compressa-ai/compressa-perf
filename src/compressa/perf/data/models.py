from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import datetime
import textwrap


class MetricName(Enum):
    # Time To First Token
    TTFT = "TTFT"

    # The 95th percentile time to first token
    TTFT_95 = "TTFT_95"

    # Time Per Output Token
    TPOT = "TPOT"

    # The overall time it takes for the model to generate the full response for a user.
    # LATENCY = (TTFT) + (TPOT) * output_length
    LATENCY = "LATENCY"

    # The 95th percentile latency
    LATENCY_95 = "LATENCY_95"

    # The number of tokens per second an inference server
    # can generate across all users and requests.
    THROUGHPUT = "THROUGHPUT"

    THROUGHPUT_INPUT_TOKENS = "THROUGHPUT_INPUT_TOKENS"

    THROUGHPUT_OUTPUT_TOKENS = "THROUGHPUT_OUTPUT_TOKENS"

    # The number of requests per second an inference server can handle.
    # RPS = num_tasks / (max(end_time) - min(start_time))
    RPS = "RPS"

    # Top 5% latency longest latency
    TOP_5_LATENCY = "TOP_5_LATENCY"
    
    # Top 5% TTFT
    TOP_5_TTFT = "TOP_5_TTFT"

    # Longer than 60 seconds latency
    LONGER_THAN_60_LATENCY = "LONGER_THAN_60_LATENCY"

    # Longer than 120 seconds latency
    LONGER_THAN_120_LATENCY = "LONGER_THAN_120_LATENCY"

    # Longer than 180 seconds latency
    LONGER_THAN_180_LATENCY = "LONGER_THAN_180_LATENCY"

    # Failed requests total
    FAILED_REQUESTS = "FAILED_REQUESTS"

    # Failed requests per hour
    FAILED_REQUESTS_PER_HOUR = "FAILED_REQUESTS_PER_HOUR"


@dataclass
class Experiment:
    id: int
    experiment_name: str
    experiment_date: datetime.datetime
    description: Optional[str] = None

    def __str__(self):
        return textwrap.dedent(
            f"""
        Experiment(
            experiment_id={self.id},
            experiment_name={self.experiment_name},
            experiment_date={self.experiment_date},
            description={self.description}
        )
        """
        )


@dataclass
class Metric:
    id: int
    experiment_id: int
    metric_name: str
    metric_value: float
    timestamp: datetime.datetime

    def __str__(self):
        return textwrap.dedent(
            f"""
        Metric(
            metric_id={self.id},
            experiment_id={self.experiment_id},
            metric_name={self.metric_name},
            metric_value={self.metric_value},
            timestamp={self.timestamp},
        )
        """
        )


@dataclass
class Parameter:
    id: int
    experiment_id: int
    key: str
    value: str

    def __str__(self):
        return textwrap.dedent(
            f"""
        Parameter(
            id={self.id},
            experiment_id={self.experiment_id},
            key={self.key},
            value={self.value}
        )
        """
        )


class Status(Enum):
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class Measurement:
    id: int
    experiment_id: int
    n_input: int
    n_output: int
    ttft: float
    start_time: float
    end_time: float
    status: Status = Status.SUCCESS

    def __str__(self):
        return textwrap.dedent(
            f"""
        Measurement(
            id={self.id},
            experiment_id={self.experiment_id},
            n_input={self.n_input},
            n_output={self.n_output},
            ttft={self.ttft},
            start_time={self.start_time},
            end_time={self.end_time},
            status={self.status}
        )
        """
        )

    @classmethod
    def failed(
        cls,
        experiment_id: int,
        n_input: int,
        n_output: int,
        ttft: float,
        start_time: float,
        end_time: float,
    ):
        return cls(
            id=None,
            experiment_id=experiment_id,
            n_input=n_input,
            n_output=n_output,
            ttft=ttft,
            start_time=start_time,
            end_time=end_time,
            status=Status.FAILED,
        )