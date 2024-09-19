from typing import List

from compressa.perf.data.metric import (
    Parameter,
    Artifact,
    Deploy,
    Metric,
    Experiment,
)


def fetch_all_experiments(conn) -> List[Experiment]:
    sql = "SELECT * FROM Experiments"
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return [Experiment(*row) for row in rows]


def fetch_metrics_by_experiment(
    conn,
    experiment_id: int
) -> List[Metric]:
    sql = "SELECT * FROM Metrics WHERE experiment_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id,))
    rows = cur.fetchall()

    metrics = []
    for row in rows:
        metric_id = row[0]
        sql_parameters = "SELECT parameters_id FROM MetricParameters WHERE metric_id = ?"
        cur.execute(sql_parameters, (metric_id,))
        param_rows = cur.fetchall()
        parameters = [param_row[0] for param_row in param_rows]
        metrics.append(
            Metric(
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                parameters
            )
        )

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


def fetch_deploy_by_id(conn, deploy_id: int) -> Deploy:
    sql = "SELECT * FROM Deploys WHERE deploy_id = ?"
    cur = conn.cursor()
    cur.execute(sql, (deploy_id,))
    row = cur.fetchone()
    return Deploy(*row) if row else None
