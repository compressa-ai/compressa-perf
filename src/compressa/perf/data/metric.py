import enum

from dataclasses import dataclass


class MetricName(enum.Enum):
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
class Metric:
    input_length: int
    output_length: int
    metric_name: str
    metric_value: float


@dataclass
class Deploy:
    deploy_id: int
    model_name: str
    hardware: str
    context_length: int
    quantization: str


@dataclass
class Experiment:
    experiment_id: int
    experiment_name: str
    experiment_date: str
    description: str


@dataclass
class Metric:
    metric_id: int
    experiment_id: int
    metric_name: str
    metric_value: float
    timestamp: str
    parameters_id: int
    deploy_id: int


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
    description: str
