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

    # The number of output tokens per second an inference server
    # can generate across all users and requests.
    THROUGHPUT = "throughput"


@dataclass
class Experiment:
    experiment_id: int
    experiment_name: str
    experiment_date: datetime.datetime
    description: Optional[str] = None

    def __str__(self):
        return textwrap.dedent(f"""
        Experiment(
            experiment_id={self.experiment_id},
            experiment_name={self.experiment_name},
            experiment_date={self.experiment_date},
            description={self.description}
        )
        """)


@dataclass
class Metric:
    metric_id: int
    experiment_id: int
    metric_name: MetricName
    metric_value: float
    timestamp: datetime.datetime
    parameters_id: Optional[int] = None

    def __str__(self):
        return textwrap.dedent(f"""
        Metric(
            metric_id={self.metric_id},
            experiment_id={self.experiment_id},
            metric_name={self.metric_name},
            metric_value={self.metric_value},
            timestamp={self.timestamp},
            parameters_id={self.parameters_id}
        )
        """)


@dataclass
class Parameter:
    parameters_id: int
    experiment_id: int
    param_key: str
    param_value: str

    def __str__(self):
        return textwrap.dedent(f"""
        Parameter(
            parameters_id={self.parameters_id},
            experiment_id={self.experiment_id},
            param_key={self.param_key},
            param_value={self.param_value}
        )
        """)


@dataclass
class Artifact:
    artifact_id: int
    experiment_id: int
    artifact_name: str
    artifact_path: str
    description: Optional[str] = None

    def __str__(self):
        return textwrap.dedent(f"""
        Artifact(
            artifact_id={self.artifact_id},
            experiment_id={self.experiment_id},
            artifact_name={self.artifact_name},
            artifact_path={self.artifact_path},
            description={self.description}
        )
        """)


@dataclass
class Measurement:
    experiment_id: int
    n_input: int
    n_output: int
    ttft: float
    total_time: float

    def __str__(self):
        return textwrap.dedent(f"""
        Measurement(
            experiment_id={self.experiment_id},
            n_input={self.n_input},
            n_output={self.n_output},
            ttft={self.ttft},
            total_time={self.total_time}
        )
        """)
