# db_operations.py

import sqlite3
from typing import List, Optional
from compressa.perf.data.models import (
    Experiment,
    Metric,
    Parameter,
    MetricName,
    Measurement,
)
import datetime
from datetime import datetime


# Insert Operations


def insert_experiment(conn, experiment: Experiment) -> int:
    sql = """
    INSERT INTO Experiments (experiment_name, description)
    VALUES (?, ?)
    """
    with conn:
        cur = conn.execute(sql, (experiment.experiment_name, experiment.description))
    return cur.lastrowid


def insert_parameter(conn, parameter: Parameter) -> int:
    sql = """
    INSERT INTO Parameters (experiment_id, key, value)
    VALUES (?, ?, ?)
    """
    with conn:
        cur = conn.execute(
            sql, (parameter.experiment_id, parameter.key, parameter.value)
        )
    return cur.lastrowid


def insert_metric(conn, metric: Metric) -> int:
    sql = """
    INSERT INTO Metrics (experiment_id, metric_name, metric_value, timestamp)
    VALUES (?, ?, ?, ?)
    """
    with conn:
        cur = conn.execute(
            sql,
            (
                metric.experiment_id,
                metric.metric_name.value,
                metric.metric_value,
                metric.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        metric.id = cur.lastrowid
    return metric


def insert_measurement(conn, measurement: Measurement) -> int:
    sql = """
    INSERT INTO Measurements (experiment_id, n_input, n_output, ttft, start_time, end_time)
    VALUES (?, ?, ?, ?, ?, ?)
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
            ),
        )
    return cur.lastrowid


# Fetch Operations


def fetch_all_experiments(conn) -> List[Experiment]:
    sql = "SELECT * FROM Experiments ORDER BY experiment_date DESC"
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return [
        Experiment(
            id=row[0],
            experiment_name=row[1],
            experiment_date=datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
            description=row[3]
        )
        for row in rows
    ]


def fetch_metrics_by_experiment(conn, experiment_id: int) -> List[Metric]:
    sql = "SELECT * FROM Metrics WHERE experiment_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id,))
    rows = cur.fetchall()
    metrics = []
    for row in rows:
        metrics.append(
            Metric(
                id=row[0],
                experiment_id=row[1],
                metric_name=MetricName(row[2]),
                metric_value=row[3],
                timestamp=datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S"),
            )
        )
    return metrics


def fetch_parameters_by_experiment(conn, experiment_id: int) -> List[Parameter]:
    sql = "SELECT * FROM Parameters WHERE experiment_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id,))
    rows = cur.fetchall()
    return [Parameter(*row) for row in rows]


def fetch_measurements_by_experiment(conn, experiment_id: int) -> List[Measurement]:
    sql = "SELECT * FROM Measurements WHERE experiment_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id,))
    rows = cur.fetchall()
    return [Measurement(*row) for row in rows]


def fetch_experiment_by_id(conn, experiment_id: int) -> Optional[Experiment]:
    sql = "SELECT * FROM Experiments WHERE id = ?"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id,))
    row = cur.fetchone()
    if row:
        return Experiment(
            id=row[0],
            experiment_name=row[1],
            experiment_date=datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
            description=row[3]
        )
    return None
