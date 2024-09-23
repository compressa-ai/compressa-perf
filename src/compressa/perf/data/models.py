from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
import datetime


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


@dataclass
class Deploy:
    deploy_id: int
    model_name: str
    hardware: str
    context_length: int
    quantization: str


@dataclass
class Metric:
    metric_id: int = None
    experiment_id: int
    metric_name: MetricName
    metric_value: float
    timestamp: datetime.datetime
    parameters_id: Optional[int] = None
    deploy_id: Optional[int] = None


@dataclass
class Parameter:
    parameters_id: int
    experiment_id: int
    param_key: str
    param_value: str


@dataclass
class Artifact:
    artifact_id: int
    experiment_id: int
    artifact_name: str
    artifact_path: str
    description: Optional[str] = None