import sqlite3
from compressa.perf.data.models import (
    Experiment,
    Metric,
    Parameter,
    Measurement,
)
from datetime import datetime

def direct_insert_experiment(conn: sqlite3.Connection, experiment: Experiment) -> int:
    sql = """
    INSERT INTO Experiments (experiment_name, description)
    VALUES (?, ?)
    """
    with conn:
        cur = conn.execute(sql, (experiment.experiment_name, experiment.description))
    return cur.lastrowid

def direct_insert_parameter(conn: sqlite3.Connection, parameter: Parameter) -> int:
    sql = """
    INSERT INTO Parameters (experiment_id, key, value)
    VALUES (?, ?, ?)
    """
    with conn:
        cur = conn.execute(
            sql,
            (parameter.experiment_id, parameter.key, parameter.value)
        )
    return cur.lastrowid

def direct_insert_metric(conn: sqlite3.Connection, metric: Metric) -> int:
    sql = """
    INSERT INTO Metrics (experiment_id, metric_name, metric_value, timestamp)
    VALUES (?, ?, ?, ?)
    """
    with conn:
        cur = conn.execute(
            sql,
            (
                metric.experiment_id,
                metric.metric_name,
                metric.metric_value,
                metric.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
    return cur.lastrowid

def direct_insert_measurement(conn: sqlite3.Connection, measurement: Measurement) -> int:
    sql = """
    INSERT INTO Measurements (
      experiment_id, n_input, n_output, ttft, start_time, end_time, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    with conn:
        cur = conn.execute(
            sql,
            (
                measurement.experiment_id,
                measurement.n_input,
                measurement.n_output,
                measurement.ttft,
                measurement.start_time,
                measurement.end_time,
                measurement.status.value,
            )
        )
    return cur.lastrowid
