import sqlite3
from tabulate import tabulate
from compressa.perf.experiment.inference import ExperimentRunner
from compressa.perf.experiment.analysis import Analyzer
from compressa.perf.data.models import Experiment
from compressa.perf.db.operations import (
    insert_experiment,
    fetch_metrics_by_experiment,
    fetch_parameters_by_experiment,
    fetch_experiment_by_id,
    fetch_all_experiments,
)
from compressa.perf.db.setup import create_tables
import datetime
import sys
import random
import string

DEFAULT_DB_PATH = "compressa-perf-db.sqlite"


def format_value(value, precision=4):
    try:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return f"{int(numeric_value):<{precision}}"
        elif numeric_value < 0.01:
            return f"{numeric_value:.{precision}e}"
        else:
            return f"{numeric_value:.{precision}f}"
    except ValueError:
        return str(value)


def ensure_db_initialized(conn):
    try:
        # Check if the Experiments table exists
        conn.execute("SELECT 1 FROM Experiments LIMIT 1")
    except sqlite3.OperationalError:
        # If the table doesn't exist, create the tables
        print("Database not initialized. Creating tables...")
        create_tables(conn)
        print("Tables created successfully.")


def generate_random_text(length):
    words = []
    current_length = 0
    while current_length < length:
        word_length = random.randint(1, 20)
        word = ''.join(random.choice(string.ascii_lowercase) for _ in range(word_length))
        words.append(word)
        current_length += len(word) + 1
    return ' '.join(words)[:length]

def generate_prompts_list(num_prompts, prompt_length):
    prompts = []
    for i in range(num_prompts):
        random_text = generate_random_text(prompt_length - len(str(i)) - 1)
        prompt = f"{i} {random_text}"
        prompts.append(prompt)
    return prompts

def run_experiment(
    db: str = DEFAULT_DB_PATH,
    openai_api_key: str = None,
    openai_url: str = None,
    model_name: str = None,
    experiment_name: str = None,
    description: str = None,
    prompts_file: str = None,
    num_tasks: int = 100,
    num_runners: int = 10,
    generate_prompts: bool = False,
    num_prompts: int = 100,
    prompt_length: int = 100
):
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    with sqlite3.connect(db) as conn:
        create_tables(conn)
        experiment_runner = ExperimentRunner(
            conn=conn,
            openai_api_key=openai_api_key,
            openai_url=openai_url,
            model_name=model_name,
            num_runners=num_runners
        )

        experiment = Experiment(
            id=None,
            experiment_name=experiment_name,
            experiment_date=datetime.datetime.now(),
            description=description,
        )
        experiment.id = insert_experiment(conn, experiment)
        print(f"Experiment created: {experiment}")

        if generate_prompts:
            prompts = generate_prompts_list(num_prompts, prompt_length)
        else:
            with open(prompts_file, 'r') as f:
                prompts = [line.strip() for line in f.readlines()]

        experiment_runner.run_experiment(
            experiment_id=experiment.id,
            prompts=prompts,
            num_tasks=num_tasks
        )

        # Run analysis after the experiment
        analyzer = Analyzer(conn)
        analyzer.compute_metrics(experiment.id)
        
        # Reuse the reporting functionality
        report_experiment(
            experiment_id=experiment.id,
            db=db,
            recompute=False
        )


def report_experiment(
    experiment_id: int,
    db: str = DEFAULT_DB_PATH,
    recompute: bool = False,
):
    with sqlite3.connect(db) as conn:
        ensure_db_initialized(conn)

        experiment = fetch_experiment_by_id(conn, experiment_id)
        if not experiment:
            print(f"Error: Experiment with ID {experiment_id} not found.")
            sys.exit(1)

        analyzer = Analyzer(conn)
        
        if recompute:
            analyzer.compute_metrics(experiment_id)
        
        parameters = fetch_parameters_by_experiment(conn, experiment_id)
        metrics = fetch_metrics_by_experiment(conn, experiment_id)
        
        print(f"\nExperiment Details:")
        print(f"ID: {experiment.id}")
        print(f"Name: {experiment.experiment_name}")
        print(f"Date: {experiment.experiment_date}")
        print(f"Description: {experiment.description}")
        
        param_table = [[p.key, format_value(p.value)] for p in parameters]
        print("\nExperiment Parameters:")
        print(tabulate(
            param_table, 
            headers=["Parameter", "Value"], 
            tablefmt="fancy_grid", 
            stralign="right",
            numalign="right",
        ))

        # Prepare metrics table with better formatting
        metrics_table = [[m.metric_name, format_value(m.metric_value)] for m in metrics]
        print("\nExperiment Metrics:")
        print(tabulate(
            metrics_table, 
            headers=["Metric", "Value"], 
            tablefmt="fancy_grid", 
            numalign="decimal",
        ))


def list_experiments(
    db: str = DEFAULT_DB_PATH,
):
    with sqlite3.connect(db) as conn:
        ensure_db_initialized(conn)

        experiments = fetch_all_experiments(conn)
        
        if not experiments:
            print("No experiments found in the database.")
            return

        table_data = [
            [
                exp.id,
                exp.experiment_name,
                exp.experiment_date.strftime("%Y-%m-%d %H:%M:%S") if exp.experiment_date else "N/A",
                exp.description[:50] + "..." if exp.description and len(exp.description) > 50 else exp.description
            ]
            for exp in experiments
        ]

        print("\nList of Experiments:")
        print(tabulate(table_data, headers=["ID", "Name", "Date", "Description"], tablefmt="grid"))


