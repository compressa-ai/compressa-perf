# db_setup.py

import sqlite3


def create_tables(conn):
    try:
        with conn:
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS Experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_name TEXT NOT NULL,
                experiment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
            """
            )
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS Parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                param_key TEXT NOT NULL,
                param_value TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
            );
            """
            )
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS Metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
            );
            """
            )
            conn.execute(
                """
            CREATE TABLE IF NOT EXISTS Measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                n_input INTEGER NOT NULL,
                n_output INTEGER NOT NULL,
                ttft REAL NOT NULL,
                total_time REAL NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
            );
            """
            )
        print("Tables created successfully")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
