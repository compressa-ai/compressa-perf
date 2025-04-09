import time
import logging
import openai
import httpx
from typing import List, Dict

from compressa.perf.data.models import (
    Measurement,
    Parameter,
    Status,
)
from compressa.perf.db.operations import (
    insert_measurement,
    insert_parameter,
)
from compressa.utils import get_logger, stream_chat

import sqlite3
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
import random
from tqdm import tqdm

logger = get_logger(__name__)


class InferenceRunner:
    def __init__(
        self,
        api_key: str,
        openai_url: str,
        model_name: str,
    ):
        self.model_name = model_name
        http_client = httpx.Client(
            limits=httpx.Limits(
                max_connections=200,
                max_keepalive_connections=100
            ),
            timeout=600.0
        )
        self.client = openai.OpenAI(api_key=api_key, base_url=openai_url, http_client=http_client)

    def run_inference(
        self,
        experiment_id: int,
        prompt: str,
        max_tokens: int,
    ):
        start_time = time.time()

        response = None
        first_token_time = -1
        end_time = -1
        ttft = 0
        n_chunks = 0
        status = Status.SUCCESS
        error_message = None
        n_input = -1
        n_output = -1
        try:
            response: openai.Stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                stream=True,
                stream_options={
                    'include_usage': True,
                },
            )

            response_text = ""
            first_token_empty = False
            chunk = None
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    if first_token_time == -1:
                        if chunk.choices[0].delta.content == "":
                            if not first_token_empty:
                                first_token_empty = True
                                continue
                            else:
                                raise Exception("First token is empty")
                        first_token_time = time.time()
                        ttft = first_token_time - start_time
                    n_chunks += 1
                    response_text += chunk.choices[0].delta.content
                elif first_token_time == -1 and chunk.choices[0].delta.content is None:
                    status = Status.FAILED
                    raise Exception("First token not found in response")
            end_time = time.time()
            logger.debug(f"Prompt: {prompt}\nResponse text: {response_text}\n{'#' * 100}")

            if not chunk:
                raise Exception("Chunk not found in response")
                
            if not chunk.usage:
                if status == Status.SUCCESS:
                    logger.error(f"Usage not found in response when success")
                    raise Exception("Usage not found in response when success")

            usage = chunk.usage
            n_input = usage.prompt_tokens
            n_output = usage.completion_tokens

            assert status == Status.SUCCESS
           
            return Measurement(
                id=None,
                experiment_id=experiment_id,
                n_input=n_input,
                n_output=n_output,
                ttft=ttft,
                start_time=start_time,
                end_time=end_time,
                status=Status.SUCCESS,
            )

        except Exception as e:
            end_time = time.time() - start_time
            logger.error(f"API request failed: {e}.\n ttft: {ttft}s, end_time: {end_time}s, n_chunks: {n_chunks} {response}")
            status = Status.FAILED
            return Measurement.failed(
                experiment_id=experiment_id,
                n_input=n_input,
                n_output=n_output,
                ttft=ttft,
                start_time=start_time,
                end_time=end_time,
            )


class ExperimentRunner:
    def __init__(
        self,
        api_key: str,
        openai_url: str,
        model_name: str,
        num_runners: int = 10,
    ):
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
            insert_parameter(param)

    def run_experiment(
        self,
        experiment_id: int,
        prompts: List[str],
        num_tasks: int = 100,
        max_tokens: int = 1000,
        seed: int = 42,
    ):
        choise_generator = random.Random(seed)
        all_measurements = []
        with ThreadPoolExecutor(max_workers=self.num_runners) as executor:
            runners = [
                InferenceRunner(
                    self.api_key,
                    self.openai_url,
                    self.model_name,
                )
                for _ in range(self.num_runners)
            ]
            futures = [
                executor.submit(
                    runners[i % self.num_runners].run_inference,
                    experiment_id,
                    choise_generator.choice(prompts),
                    max_tokens
                )
                for i in range(num_tasks)
            ]
            for future in tqdm(as_completed(futures), total=num_tasks, desc="Running experiments"):
                try:
                    result = future.result()
                    all_measurements.append(result)
                except Exception as e:
                    logger.error(f"Task failed: {e}")

        self.store_experiment_parameters(
            experiment_id,
            num_tasks,
            max_tokens,
        )

        for measurement in all_measurements:
            insert_measurement(measurement)

        logger.info(
            f"Number of failed measurements: {len([m for m in all_measurements if m.status == Status.FAILED])}"
        )
