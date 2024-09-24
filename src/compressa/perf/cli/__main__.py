import argparse
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
    fetch_all_experiments,  # Add this import
)
from compressa.perf.db.setup import create_tables
import datetime
import sys

DEFAULT_DB_PATH = "compressa-perf-db.sqlite"

def run_experiment(args):
    openai_api_key = args.openai_api_key
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    with sqlite3.connect(args.db) as conn:
        create_tables(conn)
        experiment_runner = ExperimentRunner(
            conn=conn,
            openai_api_key=openai_api_key,
            openai_url=args.openai_url,
            model_name=args.model_name,
            num_runners=args.num_runners
        )

        experiment = Experiment(
            id=None,
            experiment_name=args.experiment_name,
            experiment_date=datetime.datetime.now(),
            description=args.description,
        )
        experiment.id = insert_experiment(conn, experiment)
        print(f"Experiment created: {experiment}")

        with open(args.prompts_file, 'r') as f:
            prompts = [line.strip() for line in f.readlines()]

        experiment_runner.run_experiment(
            experiment_id=experiment.id,
            prompts=prompts,
            num_tasks=args.num_tasks
        )

        # Run analysis after the experiment
        analyzer = Analyzer(conn)
        analyzer.compute_metrics(experiment.id)
        metrics = fetch_metrics_by_experiment(conn, experiment.id)
        for metric in metrics:
            print(metric)


def report_experiment(args):
    with sqlite3.connect(args.db) as conn:
        # Check if the experiment exists
        experiment = fetch_experiment_by_id(conn, args.experiment_id)
        if not experiment:
            print(f"Error: Experiment with ID {args.experiment_id} not found.")
            sys.exit(1)

        analyzer = Analyzer(conn)
        
        if args.recompute:
            analyzer.compute_metrics(args.experiment_id)
        
        parameters = fetch_parameters_by_experiment(conn, args.experiment_id)
        metrics = fetch_metrics_by_experiment(conn, args.experiment_id)
        
        # Print experiment details
        print(f"\nExperiment Details:")
        print(f"ID: {experiment.id}")
        print(f"Name: {experiment.experiment_name}")
        print(f"Date: {experiment.experiment_date}")
        print(f"Description: {experiment.description}")
        
        # Prepare parameter table
        param_table = [[p.name, p.value] for p in parameters]
        print("\nExperiment Parameters:")
        print(tabulate(param_table, headers=["Parameter", "Value"], tablefmt="grid"))
        
        # Prepare metrics table
        metrics_table = [[m.metric_name, m.metric_value] for m in metrics]
        print("\nExperiment Metrics:")
        print(tabulate(metrics_table, headers=["Metric", "Value"], tablefmt="grid"))


def list_experiments(args):
    with sqlite3.connect(args.db) as conn:
        experiments = fetch_all_experiments(conn)
        
        if not experiments:
            print("No experiments found in the database.")
            return

        table_data = [
            [
                exp.id,
                exp.experiment_name,
                exp.experiment_date.strftime("%Y-%m-%d %H:%M:%S"),
                exp.description[:50] + "..." if exp.description and len(exp.description) > 50 else exp.description
            ]
            for exp in experiments
        ]

        print("\nList of Experiments:")
        print(tabulate(table_data, headers=["ID", "Name", "Date", "Description"], tablefmt="grid"))

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for running and analyzing experiments"
    )
    subparsers = parser.add_subparsers()

    parser_run = subparsers.add_parser(
        "measure",
        help="Run an experiment",
    )
    parser_run.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB_PATH,
        help="Path to the SQLite database",
    )
    parser_run.add_argument(
        "--openai_url", type=str, required=True, help="OpenAI API URL"
    )
    parser_run.add_argument(
        "--model_name", type=str, required=True, help="Model name"
    )
    parser_run.add_argument(
        "--experiment_name", type=str, required=True, help="Name of the experiment"
    )
    parser_run.add_argument(
        "--description", type=str, help="Description of the experiment"
    )
    parser_run.add_argument(
        "--prompts_file", type=str, required=True, help="Path to the file containing prompts"
    )
    parser_run.add_argument(
        "--num_tasks", type=int, default=100, help="Number of tasks to run"
    )
    parser_run.add_argument(
        "--num_runners", type=int, default=10, help="Number of concurrent runners"
    )
    parser_run.add_argument(
        "--openai_api_key", type=str, required=True, help="OpenAI API key"
    )
    parser_run.set_defaults(func=run_experiment)

    parser_report = subparsers.add_parser(
        "report",
        help="Generate a report for an experiment",
    )
    parser_report.add_argument(
        "experiment_id", type=int, help="ID of the experiment to report on"
    )
    parser_report.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB_PATH,
        help="Path to the SQLite database",
    )
    parser_report.add_argument(
        "--recompute",
        action="store_true",
        help="Recompute metrics before generating the report",
    )
    parser_report.set_defaults(func=report_experiment)

    parser_list = subparsers.add_parser(
        "list",
        help="List all experiments",
    )
    parser_list.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB_PATH,
        help="Path to the SQLite database",
    )
    parser_list.set_defaults(func=list_experiments)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
