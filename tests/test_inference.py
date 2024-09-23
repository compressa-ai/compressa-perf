import unittest
import sqlite3
import datetime
import os
from dotenv import load_dotenv

from compressa.perf.inference import InferenceRunner
from compressa.perf.db import DB_NAME
from compressa.perf.data.models import Experiment
from compressa.perf.db.operations import insert_experiment, fetch_metrics_by_experiment
from compressa.perf.db.setup import create_tables



class TestData(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set")

    def setUp(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        with sqlite3.connect(DB_NAME) as conn:
            create_tables(conn)

    def test_inference(self):
        with sqlite3.connect(DB_NAME) as conn:
            runner = InferenceRunner(
                conn=conn,
                openai_api_key=self.openai_api_key,
                openai_url="https://api.qdrant.mil-team.ru/chat-2/v1",
                model_name="Compressa-Llama-3.1-8B",
            )

            experiment = Experiment(
                experiment_id=None,
                experiment_name="Test Experiment",
                experiment_date=datetime.datetime.now(),
                description="This is a test experiment.",
            )
            experiment.experiment_id = insert_experiment(conn, experiment)
            print(experiment)

            runner.run_inference(
                experiment_id=experiment.experiment_id,
                prompt="Hello, world!",
            )

            metrics = fetch_metrics_by_experiment(conn, experiment.experiment_id)
            for metric in metrics:
                print(metric)
