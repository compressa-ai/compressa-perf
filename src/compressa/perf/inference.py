import time
import logging
import openai
from typing import List, Dict
from compressa.perf.data.models import MetricName, Metric
from compressa.perf.db.operations import insert_metric
import sqlite3
import datetime
import textwrap


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class InferenceRunner:
    def __init__(
        self,
        conn: sqlite3.Connection,
        openai_api_key: str,
        openai_url: str,
        model_name: str,
    ):
        self.conn = conn
        self.model_name = model_name
        self.client = openai.OpenAI(api_key=openai_api_key, base_url=openai_url)

    def run_inference(
        self,
        experiment_id: int,
        prompt: str,
        max_tokens: int = 1000,
    ):
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                stream=True,
            )
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return

        metrics = []
        first_token_time = None
        total_tokens = 0
        ttft = 0

        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                if first_token_time is None:
                    first_token_time = time.time()
                    ttft = first_token_time - start_time
                    metrics.append(
                        Metric(
                            id=None,
                            experiment_id=experiment_id,
                            metric_name=MetricName.TTFT,
                            metric_value=ttft,
                            timestamp=datetime.datetime.now(),
                        )
                    )
                total_tokens += 1

        print(f"Total tokens: {total_tokens}")
        print(f"TTFT: {ttft:.4f}s")
        end_time = time.time()
        total_time = end_time - start_time

        throughput = total_tokens / total_time if total_time > 0 else 0

        metrics.append(
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.THROUGHPUT,
                metric_value=throughput,
                timestamp=datetime.datetime.now(),
            )
        )

        metrics.append(
            Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.LATENCY,
                metric_value=total_time,
                timestamp=datetime.datetime.now(),
            )
        )

        print(
            textwrap.dedent(
                f"""
            Inference completed:
                TTFT={ttft:.4f}s,
                Total Time={total_time:.4f}s,
                Throughput={throughput:.2f} tokens/s
            """
            )
        )

        for metric in metrics:
            insert_metric(self.conn, metric)

        return metrics
