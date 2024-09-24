import unittest
import sqlite3
import datetime
import os
from dotenv import load_dotenv

from compressa.perf.experiment.inference import InferenceRunner, ExperimentRunner
from compressa.perf.db import DB_NAME
from compressa.perf.data.models import Experiment, Measurement
from compressa.perf.db.operations import insert_experiment, fetch_measurements_by_experiment, insert_measurement
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
                id=None,
                experiment_name="Test Experiment",
                experiment_date=datetime.datetime.now(),
                description="This is a test experiment.",
            )
            experiment.id = insert_experiment(conn, experiment)
            print(experiment)

            measurement = runner.run_inference(
                experiment_id=experiment.id,
                prompt="Hello, world!",
            )

            if measurement:
                insert_measurement(conn, measurement)

            measurements = fetch_measurements_by_experiment(conn, experiment.id)
            for measurement in measurements:
                print(measurement)

    def test_experiment_runner(self):
        n_tasks = 10
        with sqlite3.connect(DB_NAME) as conn:
            experiment_runner = ExperimentRunner(
                conn=conn,
                openai_api_key=self.openai_api_key,
                openai_url="https://api.qdrant.mil-team.ru/chat-2/v1",
                model_name="Compressa-Llama-3.1-8B",
                num_runners=5
            )

            experiment = Experiment(
                id=None,
                experiment_name="Test Experiment Runner",
                experiment_date=datetime.datetime.now(),
                description="This is a test experiment for ExperimentRunner.",
            )
            experiment.id = insert_experiment(conn, experiment)
            print(experiment)

            prompts = ["Hello, world!", "How are you?", "Tell me a joke."]
            experiment_runner.run_experiment(
                experiment_id=experiment.id,
                prompts=prompts,
                num_tasks=n_tasks
            )

            measurements = fetch_measurements_by_experiment(conn, experiment.id)
            self.assertEqual(len(measurements), n_tasks)
            for measurement in measurements:
                print(measurement)


if __name__ == "__main__":
    unittest.main()
