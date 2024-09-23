# db_operations.py

import sqlite3
from typing import List, Optional
from compressa.perf.data.models import (
    Experiment,
    Metric,
    Parameter,
    Artifact,
    MetricName,
)
import datetime


# Insert Operations

def insert_experiment(conn, experiment_name: str, description: Optional[str] = None) -> int:
    sql = """
    INSERT INTO Experiments (experiment_name, description)
    VALUES (?, ?)
    """
    with conn:
        cur = conn.execute(sql, (experiment_name, description))
    return cur.lastrowid


def insert_parameter(conn, experiment_id: int, param_key: str, param_value: str) -> int:
    sql = """
    INSERT INTO Parameters (experiment_id, param_key, param_value)
    VALUES (?, ?, ?)
    """
    with conn:
        cur = conn.execute(sql, (experiment_id, param_key, param_value))
    return cur.lastrowid


def insert_metric(conn, metric: Metric) -> Metric:
    sql = """
    INSERT INTO Metrics (experiment_id, metric_name, metric_value, parameters_id)
    VALUES (?, ?, ?, ?)
    """
    with conn:
        cur = conn.execute(
            sql,
            (
                metric.experiment_id,
                metric.metric_name.value,
                metric.metric_value,
                metric.parameters_id
            )
        )
        metric.metric_id = cur.lastrowid
    return metric


def insert_artifact(
    conn,
    experiment_id: int,
    artifact_name: str,
    artifact_path: str,
    description: Optional[str] = None
) -> int:
    sql = """
    INSERT INTO Artifacts (experiment_id, artifact_name, artifact_path, description)
    VALUES (?, ?, ?, ?)
    """
    with conn:
        cur = conn.execute(sql, (experiment_id, artifact_name, artifact_path, description))
    return cur.lastrowid


# Fetch Operations

def fetch_all_experiments(conn) -> List[Experiment]:
    sql = "SELECT * FROM Experiments"
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return [Experiment(*row) for row in rows]


def fetch_metrics_by_experiment(conn, experiment_id: int) -> List[Metric]:
    sql = "SELECT * FROM Metrics WHERE experiment_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id,))
    rows = cur.fetchall()
    metrics = []
    for row in rows:
        metrics.append(Metric(
            metric_id=row[0],
            experiment_id=row[1],
            metric_name=MetricName(row[2]),
            metric_value=row[3],
            timestamp=datetime.datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S'),
            parameters_id=row[5]
        ))
    return metrics


def fetch_parameters_by_experiment(conn, experiment_id: int) -> List[Parameter]:
    sql = "SELECT * FROM Parameters WHERE experiment_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id,))
    rows = cur.fetchall()
    return [Parameter(*row) for row in rows]


def fetch_artifacts_by_experiment(conn, experiment_id: int) -> List[Artifact]:
    sql = "SELECT * FROM Artifacts WHERE experiment_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id,))
    rows = cur.fetchall()
    return [Artifact(*row) for row in rows]

