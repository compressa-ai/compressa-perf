import time
import os
import json
import logging
import openai
import httpx
import requests
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
from compressa.perf.experiment.chain_client import (
    _NodeClient,
    OptimizedNodeClientManager,
    managed_stream_response,
)

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
        shared_client_manager: OptimizedNodeClientManager,
        model_name: str,
    ) -> None:
        self.model_name = model_name
        self._shared_client_manager = shared_client_manager

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Don't close the shared client manager - it's owned by ExperimentRunner
        pass

    def close(self):
        """No-op since we use shared client manager"""
        pass

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
            # Get a client from the shared pool
            client = self._shared_client_manager.get_client()
            
            resp = client.stream_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                max_tokens=max_tokens,
            )

            # Use context manager for proper resource cleanup
            with managed_stream_response(resp) as response:
                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue

                    if raw_line.startswith("data:"):
                        raw_line = raw_line[len("data:"):].strip()

                    if raw_line == "[DONE]":
                        break

                    try:
                        chunk = json.loads(raw_line)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON: {raw_line}")
                        continue

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

        except requests.exceptions.ConnectionError as exc:
            logger.error(
                "Connection error: %s (chunks=%s, ttft=%.3fs) - consider reducing concurrency", 
                exc, n_chunks, ttft
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
        account_address: str = None,
        private_key_hex: str = None,
        num_runners: int = 10,
        no_sign: bool = False,
        old_sign: bool = False,
    ) -> None:
        self.node_url = node_url
        self.model_name = model_name
        self.account_address = account_address
        self.private_key_hex = private_key_hex
        self.num_runners = num_runners
        self.no_sign = no_sign
        self.old_sign = old_sign
        
        # Create ONE shared client manager for all runners
        # Scale clients based on number of runners
        num_clients = min(10, max(3, num_runners // 20))  # 3-10 clients based on runner count
        max_connections_per_client = 50
        
        logger.info(f"Creating shared client manager with {num_clients} clients, {max_connections_per_client} connections each for {num_runners} runners")
        
        self._shared_client_manager = OptimizedNodeClientManager(
            node_url=node_url,
            account_address=account_address,
            private_key_hex=private_key_hex,
            no_sign=no_sign,
            old_sign=old_sign,
            num_clients=num_clients,
            max_connections_per_client=max_connections_per_client,
        )

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
            ("no_sign", str(self.no_sign)),
            ("old_sign", str(self.old_sign)),
            ("client_architecture", "shared_pool"),  # Now using shared pool
        ]

        if self.account_address:
            params.append(("requester_address", self.account_address))
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

        # Create runners that share the same client manager
        runners = []
        for _ in range(self.num_runners):
            runner = InferenceRunner(
                shared_client_manager=self._shared_client_manager,
                model_name=self.model_name,
            )
            runners.append(runner)

        try:
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

        finally:
            # Close the shared client manager
            self._shared_client_manager.close_all()

        # Persist metadata & results --------------------------------------
        self._store_experiment_parameters(experiment_id, num_tasks, max_tokens)
        for m in all_measurements:
            insert_measurement(m)

        logger.info(
            "Number of failed measurements: %d",
            len([m for m in all_measurements if m.status == Status.FAILED]),
        )
