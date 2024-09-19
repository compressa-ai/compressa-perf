from dataclasses import dataclass
from typing import List


@dataclass
class Inference:
    experiment_id: str

    input: str
    output: str

    input_tokens: List[str]
    output_tokens: List[str]
    execution_time: float

    model_name: str
    hardware_id: str
