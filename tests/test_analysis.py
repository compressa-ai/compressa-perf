import unittest
import sqlite3
import time
import datetime
from compressa.perf.data.models import Experiment, Measurement
from compressa.perf.db.setup import create_tables
from compressa.perf.db.operations import insert_experiment, insert_measurement
from compressa.perf.experiment.analysis import Analyzer

class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        create_tables(self.conn)

        self.experiment = Experiment(
            id=None,
            experiment_name="Test Experiment",
            experiment_date=datetime.datetime.now(),
            description="This is a test experiment."
        )
        self.experiment.id = insert_experiment(self.conn, self.experiment)
        time_ = time.time()

        self.measurements = [
            Measurement(
                id=None,
                experiment_id=self.experiment.id,
                n_input=10,
                n_output=20,
                ttft=0.5,
                start_time=time_,
                end_time=time_ + 1.5
            ),
            Measurement(
                id=None,
                experiment_id=self.experiment.id,
                n_input=15,
                n_output=25,
                ttft=0.6,
                start_time=time_,
                end_time=time_ + 2.0
            ),
            Measurement(
                id=None,
                experiment_id=self.experiment.id,
                n_input=20,
                n_output=30,
                ttft=0.7,
                start_time=time_,
                end_time=time_ + 2.5
            )
        ]

        for measurement in self.measurements:
            insert_measurement(self.conn, measurement)

    def test_compute_metrics(self):
        analyzer = Analyzer(self.conn)
        metrics = analyzer.compute_metrics(self.experiment.id)

        self.assertAlmostEqual(metrics["average_ttft"], 0.6, places=2)
        self.assertAlmostEqual(metrics["average_latency"], 2.0, places=2)
        self.assertAlmostEqual(metrics["average_time_per_output_token"], 0.08, places=4)
        self.assertAlmostEqual(metrics["throughput"], 48.0, places=2)

if __name__ == "__main__":
    unittest.main()
