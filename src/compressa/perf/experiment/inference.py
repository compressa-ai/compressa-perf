import time
import logging
import openai
from typing import List, Dict
from compressa.perf.data.models import (
    Measurement,
    Parameter,
)
from compressa.perf.db.operations import (
    insert_measurement,
    insert_parameter,
)
import sqlite3
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
import random


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class InferenceRunner:
    def __init__(
        self,
        conn: sqlite3.Connection,
        api_key: str,
        openai_url: str,
        model_name: str,
    ):
        self.conn = conn
        self.model_name = model_name
        self.client = openai.OpenAI(api_key=api_key, base_url=openai_url)

    def run_inference(
        self,
        experiment_id: int,
        prompt: str,
        max_tokens: int,
    ):
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                stream=True,
                stream_options={
                    'include_usage': True,
                },
            )
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

        first_token_time = None
        ttft = 0

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                if first_token_time is None:
                    first_token_time = time.time()
                    ttft = first_token_time - start_time

        end_time = time.time()

        if not chunk.usage:
            logger.error(f"Usage not found in response")
            raise Exception("Usage not found in response")
            
        usage = chunk.usage
        n_input = usage.prompt_tokens
        n_output = usage.completion_tokens

        measurement = Measurement(
            id=None,
            experiment_id=experiment_id,
            n_input=n_input,
            n_output=n_output,
            ttft=ttft,
            start_time=start_time,
            end_time=end_time
        )

        return measurement


class ExperimentRunner:
    def __init__(
        self,
        conn: sqlite3.Connection,
        api_key: str,
        openai_url: str,
        model_name: str,
        num_runners: int = 10,
    ):
        self.conn = conn
        self.api_key = api_key
        self.openai_url = openai_url
        self.model_name = model_name
        self.num_runners = num_runners

    def store_experiment_parameters(
        self,
        experiment_id: int,
        num_tasks: int,
        max_tokens: int,
    ):
        parameters = [
            Parameter(
                id=None,
                experiment_id=experiment_id,
                key="num_workers",
                value=str(self.num_runners),
            ),
            Parameter(
                id=None,
                experiment_id=experiment_id,
                key="num_tasks",
                value=str(num_tasks),
            ),
            Parameter(
                id=None,
                experiment_id=experiment_id,
                key="openai_url",
                value=self.openai_url,
            ),
            Parameter(
                id=None,
                experiment_id=experiment_id,
                key="max_tokens",
                value=str(max_tokens),
            ),
            Parameter(
                id=None,
                experiment_id=experiment_id,
                key="model_name",
                value=self.model_name,
            ),
        ]
        for param in parameters:
            insert_parameter(self.conn, param)

    def run_experiment(
        self,
        experiment_id: int,
        prompts: List[str],
        num_tasks: int = 100,
        max_tokens: int = 1000,
    ):
        all_measurements = []
        with ThreadPoolExecutor(max_workers=self.num_runners) as executor:
            runners = [
                InferenceRunner(
                    self.conn,
                    self.api_key,
                    self.openai_url,
                    self.model_name,
                )
                for _ in range(self.num_runners)
            ]
            futures = [
                executor.submit(runners[i % self.num_runners].run_inference, experiment_id, random.choice(prompts), max_tokens)
                for i in range(num_tasks)
            ]
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        all_measurements.append(result)
                except Exception as e:
                    logger.error(f"Task failed: {e}")

        self.store_experiment_parameters(
            experiment_id,
            num_tasks,
            max_tokens,
        )
        for measurement in all_measurements:
            insert_measurement(self.conn, measurement)
