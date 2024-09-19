import sqlite3

create_experiments_table = """
CREATE TABLE IF NOT EXISTS Experiments (
    experiment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_name TEXT NOT NULL,
    experiment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
"""

create_metrics_table = """
CREATE TABLE IF NOT EXISTS Metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    deploy_id INTEGER,
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id),
    FOREIGN KEY (deploy_id) REFERENCES Deploys(deploy_id)
);
"""

create_parameters_table = """
CREATE TABLE IF NOT EXISTS Parameters (
    parameters_id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER,
    param_key TEXT NOT NULL,
    param_value TEXT NOT NULL,
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
);
"""

create_metric_parameters_table = """
CREATE TABLE IF NOT EXISTS MetricParameters (
    metric_id INTEGER,
    parameters_id INTEGER,
    FOREIGN KEY (metric_id) REFERENCES Metrics(metric_id),
    FOREIGN KEY (parameters_id) REFERENCES Parameters(parameters_id),
    PRIMARY KEY (metric_id, parameters_id)
);
"""

create_artifacts_table = """
CREATE TABLE IF NOT EXISTS Artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER,
    artifact_name TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
);
"""

create_deploys_table = """
CREATE TABLE IF NOT EXISTS Deploys (
    deploy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    hardware TEXT NOT NULL,
    context_length INTEGER NOT NULL,
    quantization TEXT NOT NULL
);
"""


def create_request_table(conn):
    try:
        conn.execute(create_experiments_table)
        conn.execute(create_metrics_table)
        conn.execute(create_parameters_table)
        conn.execute(create_metric_parameters_table)
        conn.execute(create_artifacts_table)
        conn.execute(create_deploys_table)
        print("Tables created successfully")
    except sqlite3.Error as e:
        print(f"The error '{e}' occurred")
