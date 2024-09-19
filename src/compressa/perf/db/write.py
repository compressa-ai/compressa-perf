from typing import List


def insert_experiment(
    conn,
    experiment_name: str,
    description: str,
) -> int:
    sql = "INSERT INTO Experiments (experiment_name, description) VALUES (?, ?)"
    cur = conn.cursor()
    cur.execute(sql, (experiment_name, description))
    conn.commit()
    return cur.lastrowid


def insert_deploy(
    conn,
    model_name: str,
    hardware: str,
    context_length: int,
    quantization: str,
) -> int:
    sql = "INSERT INTO Deploys (model_name, hardware, context_length, quantization) VALUES (?, ?, ?, ?)"
    cur = conn.cursor()
    cur.execute(sql, (model_name, hardware, context_length, quantization))
    conn.commit()
    return cur.lastrowid


def insert_metric_with_parameters(
    conn,
    experiment_id: int,
    metric_name: str,
    metric_value: float,
    deploy_id: int,
    parameters_ids: List[int],
) -> int:
    sql_metric = """
    INSERT INTO Metrics (experiment_id, metric_name, metric_value, deploy_id) 
    VALUES (?, ?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql_metric, (experiment_id, metric_name, metric_value, deploy_id))
    metric_id = cur.lastrowid

    for param_id in parameters_ids:
        sql_junction = "INSERT INTO MetricParameters (metric_id, parameters_id) VALUES (?, ?)"
        cur.execute(sql_junction, (metric_id, param_id))

    conn.commit()
    return metric_id


def insert_parameter(
    conn,
    experiment_id: int,
    param_key: str,
    param_value: str,
) -> int:
    sql = "INSERT INTO Parameters (experiment_id, param_key, param_value) VALUES (?, ?, ?)"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id, param_key, param_value))
    conn.commit()
    return cur.lastrowid


def insert_artifact(
    conn,
    experiment_id: int,
    artifact_name: str,
    artifact_path: str,
    description: str,
) -> int:
    sql = "INSERT INTO Artifacts (experiment_id, artifact_name, artifact_path, description) VALUES (?, ?, ?, ?)"
    cur = conn.cursor()
    cur.execute(sql, (experiment_id, artifact_name, artifact_path, description))
    conn.commit()
    return cur.lastrowid
