import unittest
import sqlite3

from compressa.perf.db import (
    create_request_table,
    DB_NAME,
)
from compressa.perf.db.read import fetch_all_experiments, fetch_metrics_by_experiment, fetch_parameters_by_experiment, \
    fetch_artifacts_by_experiment, fetch_deploy_by_id
from compressa.perf.db.write import insert_experiment, insert_deploy, insert_parameter, insert_metric_with_parameters, \
    insert_artifact


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        with sqlite3.connect(DB_NAME) as conn:
            create_request_table(conn)

    def tearDown(self):
        pass
        # with sqlite3.connect(DB_NAME) as conn:
        #     conn.execute("DROP TABLE Experiments")
        #     conn.execute("DROP TABLE Metrics")
        #     conn.execute("DROP TABLE Parameters")
        #     conn.execute("DROP TABLE MetricParameters")
        #     conn.execute("DROP TABLE Artifacts")
        #     conn.execute("DROP TABLE Deploys")


    def test_create_db(self):
        with sqlite3.connect(DB_NAME) as conn:
            create_request_table(conn)
            # Insert example data
            experiment_id = insert_experiment(conn, "Test Experiment 1", "This is a test experiment.")
            deploy_id = insert_deploy(conn, "ModelX", "GPU", 512, "8-bit")
            parameters_id_1 = insert_parameter(conn, experiment_id, "param1", "value1")
            parameters_id_2 = insert_parameter(conn, experiment_id, "param2", "value2")
            metric_id = insert_metric_with_parameters(conn, experiment_id, "latency", 123.45, deploy_id,
                                                      [parameters_id_1, parameters_id_2])
            artifact_id = insert_artifact(conn, experiment_id, "artifact1", "/path/to/artifact", "Artifact description")

            # Read and print data
            print("Experiments:", fetch_all_experiments(conn))
            print("Metrics for Experiment 1:", fetch_metrics_by_experiment(conn, experiment_id))
            print("Parameters for Experiment 1:", fetch_parameters_by_experiment(conn, experiment_id))
            print("Artifacts for Experiment 1:", fetch_artifacts_by_experiment(conn, experiment_id))
            print("Deploy for Metric 1:", fetch_deploy_by_id(conn, deploy_id))
