# db_setup.py

import sqlite3

def create_tables(conn):
    try:
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Experiments (
                experiment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_name TEXT NOT NULL,
                experiment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Parameters (
                parameters_id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                param_key TEXT NOT NULL,
                param_value TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                parameters_id INTEGER,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id),
                FOREIGN KEY (parameters_id) REFERENCES Parameters(parameters_id)
            );
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS Artifacts (
                artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                artifact_name TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
            );
            """)
        print("Tables created successfully")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
