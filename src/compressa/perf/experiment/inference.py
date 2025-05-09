import time
import os
import json
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
from compressa.perf.experiment.chain_client import _NodeClient

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
        node_url: str,
        model_name: str,
        account_address: str,
        private_key_hex: str,
    ) -> None:
        self.model_name = model_name
        self._client = _NodeClient(
            node_url=node_url,
            account_address=account_address,
            private_key_hex=private_key_hex,
        )

    # ---------------------------------------------------------------------
    # Public
    # ---------------------------------------------------------------------
    def run_inference(
        self,
        experiment_id: int,
        prompt: str,
        max_tokens: int,
    ) -> Measurement:
        start_time = time.time()
        first_token_time = -1.0
        ttft = 0.0
        n_chunks = 0
        n_input = 0
        n_output = 0
        response_text = ""
        status = Status.SUCCESS

        try:
            resp = self._client.stream_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                max_tokens=max_tokens,
            )

            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue

                if raw_line.startswith("data:"):
                    raw_line = raw_line[len("data:"):].strip()

                if raw_line == "[DONE]":
                    break

                chunk = json.loads(raw_line)

                usage = chunk.get("usage")
                if usage:  # present on final chunk
                    n_input = usage.get("prompt_tokens", 0)
                    n_output = usage.get("completion_tokens", 0)

                delta = (
                    chunk.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content") if chunk.get("choices") else None
                )
                logger.debug(f"Delta: {delta}")
                if delta is not None:
                    if first_token_time < 0:
                        first_token_time = time.time()
                        ttft = first_token_time - start_time
                    response_text += delta
                    n_chunks += 1

            if n_chunks == 0:
                raise RuntimeError("No content chunks received – server returned empty stream")

            end_time = time.time()
            logger.debug(
                "Prompt:%s\nResponse text:%s\n%s",
                prompt,
                response_text,
                "#" * 40,
            )

            return Measurement(
                id=None,
                experiment_id=experiment_id,
                n_input=n_input,
                n_output=n_output,
                ttft=ttft,
                start_time=start_time,
                end_time=end_time,
                status=status,
            )

        except Exception as exc:
            logger.error(
                "API request failed: %s (chunks=%s, ttft=%.3fs)", exc, n_chunks, ttft
            )
            end_time = time.time()
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
        node_url: str,
        model_name: str,
        account_address: str,
        private_key_hex: str,
        num_runners: int = 10,
    ) -> None:
        self.node_url = node_url
        self.model_name = model_name
        self.account_address = account_address
        self.private_key_hex = private_key_hex
        self.num_runners = num_runners

    def _store_experiment_parameters(
        self,
        experiment_id: int,
        num_tasks: int,
        max_tokens: int,
    ) -> None:
        params = [
            ("num_workers", str(self.num_runners)),
            ("num_tasks", str(num_tasks)),
            ("node_url", self.node_url),
            ("max_tokens", str(max_tokens)),
            ("model_name", self.model_name),
            ("requester_address", self.account_address),
        ]
        for key, value in params:
            insert_parameter(
                Parameter(id=None, experiment_id=experiment_id, key=key, value=value)
            )

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def run_experiment(
        self,
        *,
        experiment_id: int,
        prompts: List[str],
        num_tasks: int = 100,
        max_tokens: int = 1000,
        seed: int = 42,
    ) -> None:

        rng = random.Random(seed)
        all_measurements: List[Measurement] = []

        # Spin up a pool of pre‑initialised runners so each thread has its own Session
        runners = [
            InferenceRunner(
                self.node_url,
                self.model_name,
                self.account_address,
                self.private_key_hex,
            )
            for _ in range(self.num_runners)
        ]

        with ThreadPoolExecutor(max_workers=self.num_runners) as pool:
            futures = [
                pool.submit(
                    runners[i % self.num_runners].run_inference,
                    experiment_id,
                    rng.choice(prompts),
                    max_tokens,
                )
                for i in range(num_tasks)
            ]

            for f in tqdm(as_completed(futures), total=num_tasks, desc="Running experiments"):
                try:
                    all_measurements.append(f.result())
                except Exception as exc:
                    logger.error("Task failed: %s", exc)

        # Persist metadata & results --------------------------------------
        self._store_experiment_parameters(experiment_id, num_tasks, max_tokens)
        for m in all_measurements:
            insert_measurement(m)

        logger.info(
            "Number of failed measurements: %d",
            len([m for m in all_measurements if m.status == Status.FAILED]),
        )
