import sqlite3
from tabulate import tabulate
from typing import List
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
from compressa.perf.experiment.config import load_yaml_configs, ExperimentConfig

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
    
    words.append(". Repeat this text at least 10 times. Number the repetitions.")
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
    api_key: str = None,
    openai_url: str = None,
    model_name: str = None,
    experiment_name: str = None,
    description: str = None,
    prompts_file: str = None,
    num_tasks: int = 100,
    num_runners: int = 10,
    generate_prompts: bool = False,
    num_prompts: int = 100,
    prompt_length: int = 100,
    max_tokens: int = 1000,
):
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    with sqlite3.connect(db) as conn:
        create_tables(conn)
        experiment_runner = ExperimentRunner(
            conn=conn,
            api_key=api_key,
            openai_url=openai_url,
            model_name=model_name,
            num_runners=num_runners,
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
            num_tasks=num_tasks,
            max_tokens=max_tokens,
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
    show_parameters: bool = False,
    show_metrics: bool = False,
    name_filter: str = None,
    param_filters: str = None,
):
    with sqlite3.connect(db) as conn:
        ensure_db_initialized(conn)

        experiments = fetch_all_experiments(conn)
        
        if name_filter:
            experiments = [exp for exp in experiments if name_filter in exp.experiment_name]
        
        if param_filters:
            for param_filter in param_filters:
                param_key, _, param_value_substring = param_filter.partition('=')
                experiments = [exp for exp in experiments if any(
                    p.key == param_key and param_value_substring in format_value(p.value)
                    for p in fetch_parameters_by_experiment(conn, exp.id)
                )]

        if not experiments:
            print("No experiments found in the database.")
            return

        table_data = []
        headers = ["ID", "Name", "Date", "Description"]

        if show_parameters:
            headers.extend(["Parameters"])

        desciptiont_length = 20 if show_parameters or show_metrics else 50
        for exp in experiments:
            row = [
                exp.id,
                exp.experiment_name,
                exp.experiment_date.strftime("%Y-%m-%d %H:%M:%S") if exp.experiment_date else "N/A",
                exp.description[:desciptiont_length] + "..." if exp.description and len(exp.description) > desciptiont_length else exp.description
            ]

            if show_parameters:
                parameters = fetch_parameters_by_experiment(conn, exp.id)
                param_str = "\n".join([
                    f"{p.key}: {format_value(p.value, precision=2)[:10] + '...' if len(format_value(p.value, precision=2)) > 10 else format_value(p.value, precision=2)}" 
                    for p in parameters
                ])
                row.append(param_str)

            if show_metrics:
                metrics = fetch_metrics_by_experiment(conn, exp.id)
                metrics_str = "\n".join([f"{m.metric_name.value}: {format_value(m.metric_value)}" for m in metrics])
                row.append(metrics_str)

            table_data.append(row)

        print("\nList of Experiments:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))



def run_experiments_from_yaml(
    yaml_file: str,
    db: str = DEFAULT_DB_PATH,
    api_key: str = None,
):
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    configs = load_yaml_configs(yaml_file)
    
    for config in configs:
        run_experiment(
            db=db,
            api_key=api_key,
            openai_url=config.openai_url,
            model_name=config.model_name,
            experiment_name=config.experiment_name,
            description=config.description,
            prompts_file=config.prompts_file,
            num_tasks=config.num_tasks,
            num_runners=config.num_runners,
            generate_prompts=config.generate_prompts,
            num_prompts=config.num_prompts,
            prompt_length=config.prompt_length,
            max_tokens=config.max_tokens,
        )
    
    # List experiments after running them
    list_experiments(db=db)
