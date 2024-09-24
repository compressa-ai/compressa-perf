import unittest
import time
import sqlite3
import datetime

from compressa.perf.db import (
    DB_NAME,
)
from compressa.perf.db.setup import create_tables
from compressa.perf.db.operations import (
    insert_experiment,
    insert_parameter,
    insert_metric,
    insert_measurement,
    fetch_all_experiments,
    fetch_metrics_by_experiment,
    fetch_parameters_by_experiment,
    fetch_measurements_by_experiment,
)
from compressa.perf.data.models import (
    Experiment,
    Metric,
    MetricName,
    Parameter,
    Measurement
)


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        with sqlite3.connect(DB_NAME) as conn:
            create_tables(conn)

    def tearDown(self):
        pass

    def test_create_db(self):
        with sqlite3.connect(DB_NAME) as conn:
            create_tables(conn)
            # Insert example data
            experiment = Experiment(
                id=None,
                experiment_name="Test Experiment 1",
                experiment_date=datetime.datetime.now(),
                description="This is a test experiment."
            )
            experiment_id = insert_experiment(conn, experiment)
            parameter1 = Parameter(
                id=None,
                experiment_id=experiment_id,
                param_key="param1",
                param_value="value1"
            )
            parameter2 = Parameter(
                id=None,
                experiment_id=experiment_id,
                param_key="param2",
                param_value="value2"
            )
            parameters_id_1 = insert_parameter(conn, parameter1)
            parameters_id_2 = insert_parameter(conn, parameter2)

            measurement = Measurement(
                id=None,
                experiment_id=experiment_id,
                n_input=100,
                n_output=100,
                ttft=0.123,
                start_time=time.time(),
                end_time=time.time() + 0.123,
            )

            metric = Metric(
                id=None,
                experiment_id=experiment_id,
                metric_name=MetricName.TTFT,
                metric_value=0.123,
                timestamp=datetime.datetime.now(),
            )

            metric_id = insert_metric(conn, metric)
            measurement_id = insert_measurement(conn, measurement)

            print("Experiments:", fetch_all_experiments(conn))
            print("Metrics for Experiment 1:", fetch_metrics_by_experiment(conn, experiment_id))
            print("Parameters for Experiment 1:", fetch_parameters_by_experiment(conn, experiment_id))
            print("Measurements for Experiment 1:", fetch_measurements_by_experiment(conn, experiment_id))

    def test_insert_measurement(self):
        with sqlite3.connect(DB_NAME) as conn:
            create_tables(conn)
            experiment = Experiment(
                id=None,
                experiment_name="Test Experiment 2",
                experiment_date=datetime.datetime.now(),
                description="This is another test experiment."
            )
            experiment_id = insert_experiment(conn, experiment)
            measurement = Measurement(
                id=None,
                experiment_id=experiment_id,
                n_input=200,
                n_output=150,
                ttft=0.456,
                start_time=time.time(),
                end_time=time.time() + 0.456,
            )
            measurement_id = insert_measurement(conn, measurement)
            measurements = fetch_measurements_by_experiment(conn, experiment_id)
            self.assertEqual(len(measurements), 1)
            self.assertEqual(measurements[0].experiment_id, experiment_id)
            self.assertEqual(measurements[0].n_input, 200)
            self.assertEqual(measurements[0].n_output, 150)
            self.assertEqual(measurements[0].ttft, 0.456)


if __name__ == '__main__':
    unittest.main()
