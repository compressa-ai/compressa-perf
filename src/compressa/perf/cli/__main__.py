import argparse
import sqlite3
import os
from compressa.perf.experiment.inference import ExperimentRunner
from compressa.perf.experiment.analysis import Analyzer
from compressa.perf.data.models import Experiment
from compressa.perf.db.operations import insert_experiment, fetch_metrics_by_experiment
from compressa.perf.db.setup import create_tables
import datetime

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


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for running and analyzing experiments"
    )
    subparsers = parser.add_subparsers()

    parser_run = subparsers.add_parser(
        "run",
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

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
