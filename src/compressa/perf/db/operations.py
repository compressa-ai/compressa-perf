from typing import List, Optional, Callable, Any
import datetime
from datetime import datetime
import sqlite3
import time

from compressa.perf.db.setup import get_db_writer
from compressa.perf.data.models import (
    Experiment,
    Metric,
    Parameter,
    MetricName,
    Measurement,
    Status,
)


def _execute_with_retry(func: Callable[[], Any], max_retries: int = 5, initial_delay: float = 0.1) -> Any:
    """Execute a database operation with retry logic for handling database locks."""
    retry_delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return func()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            raise


def insert_parameter(parameter: Parameter) -> int:
    db_writer = get_db_writer()
    if db_writer is None:
        raise ValueError("DB writer is not initialized")
    
    db_writer.push_parameter(parameter)
    return -1



def insert_metric(metric: Metric) -> int:
    db_writer = get_db_writer()
    if db_writer is None:
        raise ValueError("DB writer is not initialized")
    
    db_writer.push_metric(metric)
    return -1


def insert_measurement(measurement: Measurement) -> int:
    db_writer = get_db_writer()
    if db_writer is None:
        raise ValueError("DB writer is not initialized")
    
    db_writer.push_measurement(measurement)
    return -1


# Fetch Operations


def fetch_all_experiments(conn) -> List[Experiment]:
    sql = "SELECT * FROM Experiments ORDER BY experiment_date DESC"
    cur = conn.cursor()
    
    def _execute():
        cur.execute(sql)
        return cur.fetchall()
    
    rows = _execute_with_retry(_execute)
    
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
    
    def _execute():
        cur.execute(sql, (experiment_id,))
        return cur.fetchall()
    
    rows = _execute_with_retry(_execute)
    
    metrics = []
    for row in rows:
        metrics.append(
            Metric(
                id=row[0],
                experiment_id=row[1],
                metric_name=row[2],
                metric_value=row[3],
                timestamp=datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S"),
            )
        )
    return metrics

def clear_metrics_by_experiment(conn, experiment_id: int) -> None:
    sql = "DELETE FROM Metrics WHERE experiment_id = ?"
    with conn:
        conn.execute(sql, (experiment_id,))

def fetch_parameters_by_experiment(conn, experiment_id: int) -> List[Parameter]:
    sql = "SELECT * FROM Parameters WHERE experiment_id = ?"
    cur = conn.cursor()
    
    def _execute():
        cur.execute(sql, (experiment_id,))
        return cur.fetchall()
    
    rows = _execute_with_retry(_execute)
    
    return [Parameter(*row) for row in rows]


def fetch_measurements_by_experiment(conn, experiment_id: int) -> List[Measurement]:
    sql = "SELECT * FROM Measurements WHERE experiment_id = ?"
    cur = conn.cursor()
    
    def _execute():
        cur.execute(sql, (experiment_id,))
        return cur.fetchall()
    
    rows = _execute_with_retry(_execute)
    
    measurements = []
    for row in rows:
        measurements.append(Measurement(
            id=row[0],
            experiment_id=row[1],
            n_input=row[2],
            n_output=row[3],
            ttft=row[4],
            start_time=row[5],
            end_time=row[6],
            status=Status(row[7]),
        ))
    return measurements


def fetch_experiment_by_id(conn, experiment_id: int) -> Optional[Experiment]:
    sql = "SELECT * FROM Experiments WHERE id = ?"
    cur = conn.cursor()
    
    def _execute():
        cur.execute(sql, (experiment_id,))
        return cur.fetchone()
    
    row = _execute_with_retry(_execute)
    
    if row:
        return Experiment(
            id=row[0],
            experiment_name=row[1],
            experiment_date=datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
            description=row[3]
        )
    return None
