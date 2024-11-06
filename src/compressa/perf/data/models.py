from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import datetime
import textwrap


class MetricName(Enum):
    # Time To First Token
    TTFT = "ttft"

    # Time Per Output Token
    TPOT = "tpot"

    # The overall time it takes for the model to generate the full response for a user.
    # LATENCY = (TTFT) + (TPOT) * output_length
    LATENCY = "latency"

    # The number of tokens per second an inference server
    # can generate across all users and requests.
    THROUGHPUT = "throughput"

    THROUGHPUT_INPUT_TOKENS = "throughput_input_tokens"

    THROUGHPUT_OUTPUT_TOKENS = "throughput_output_tokens"


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
    metric_name: MetricName
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


@dataclass
class Measurement:
    id: int
    experiment_id: int
    n_input: int
    n_output: int
    ttft: float
    start_time: float
    end_time: float

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
            end_time={self.end_time}
        )
        """
        )
