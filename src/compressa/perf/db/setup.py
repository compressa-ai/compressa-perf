from compressa.perf.db.writer import DBWriterThread

_db_writer_singleton: DBWriterThread = None

def create_tables(conn):
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_name TEXT NOT NULL,
                experiment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS Parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(id)
            );
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS Metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(id)
            );
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS Measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                n_input INTEGER NOT NULL,
                n_output INTEGER NOT NULL,
                ttft REAL NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES Experiments(id)
            );
        """)
    print("Tables created successfully.")

def start_db_writer(db_path: str):
    """
    Initializes the global DBWriterThread if it's not already started.
    """
    global _db_writer_singleton
    if _db_writer_singleton is None:
        _db_writer_singleton = DBWriterThread(db_path)
        _db_writer_singleton.start()

def stop_db_writer():
    """
    Stops the global DBWriterThread if it exists.
    """
    global _db_writer_singleton
    if _db_writer_singleton is not None:
        _db_writer_singleton.stop()
        _db_writer_singleton = None

def get_db_writer() -> DBWriterThread:
    """
    Returns the global DBWriterThread instance, or None if not started.
    """
    global _db_writer_singleton
    return _db_writer_singleton
