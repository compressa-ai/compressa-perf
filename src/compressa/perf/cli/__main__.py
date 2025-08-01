import argparse
import signal
import sys
from typing import List
from compressa.perf.cli.tools import (
    run_experiment,
    report_experiment,
    list_experiments,
    run_experiments_from_yaml,
    run_continuous_stress_test,
    DEFAULT_DB_PATH,
)
from compressa.perf.db.setup import (
    stop_db_writer,
    get_db_writer,
)


def handle_stop_signals(signum, frame):
    print(f"Received signal {signum}, stopping DB writer...")
    db_writer = get_db_writer()
    db_writer.wait_for_write()
    stop_db_writer()
    sys.exit(0)


def run_experiment_args(args):
    run_experiment(
        db=args.db,
        api_key=args.api_key,
        openai_url=args.openai_url,
        serv_api_url=args.serv_api_url,
        model_name=args.model_name,
        experiment_name=args.experiment_name,
        description=args.description,
        prompts_file=args.prompts_file,
        report_file=args.report_file,
        report_mode=args.report_mode,
        num_tasks=args.num_tasks,
        num_runners=args.num_runners,
        generate_prompts=args.generate_prompts,
        num_prompts=args.num_prompts,
        prompt_length=args.prompt_length,
        max_tokens=args.max_tokens
    )


def report_experiment_args(args):
    report_experiment(
        experiment_id=args.experiment_id,
        db=args.db,
        recompute=args.recompute
    )


def list_experiments_args(args):
    list_experiments(
        db=args.db,
        show_parameters=args.show_parameters,
        show_metrics=args.show_metrics,
        name_filter=args.name_filter,
        param_filters=args.param_filter,
        recompute=args.recompute,
        csv_file=args.csv_file,
    )


def run_experiments_from_yaml_args(args):
    run_experiments_from_yaml(
        yaml_file=args.yaml_file,
        db=args.db,
        api_key=args.api_key
    )


def run_continuous_stress_test_args(args):
    run_continuous_stress_test(
        db=args.db,
        api_key=args.api_key,
        openai_url=args.openai_url,
        model_name=args.model_name,
        experiment_name=args.experiment_name,
        description=args.description,
        prompts_file=args.prompts_file,
        serv_api_url=args.serv_api_url,
        report_file=args.report_file,
        report_mode=args.report_mode,
        num_runners=args.num_runners,
        generate_prompts=args.generate_prompts,
        num_prompts=args.num_prompts,
        prompt_length=args.prompt_length,
        max_tokens=args.max_tokens,
        report_freq_min=args.report_freq_min,
    )

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for running and analyzing experiments",
        epilog="""
Examples:
1. Run experiment with prompts from a file:
    ```
    compressa-perf measure \\
        --openai_url https://api.qdrant.mil-team.ru/chat-2/v1/ \\
        --serv_api_url "${SERV_API_URL}" \\
        --api_key "${OPENAI_API_KEY}" \\
        --model_name Compressa-Qwen2.5-14B-Instruct \\
        --experiment_name "File Prompts Run" \\
        --prompts_file resources/prompts.csv \\
        --report_file experiment \\
        --report_mode pdf \\
        --num_tasks 1000 \\
        --num_runners 100
    ```
2. Run experiment with generated prompts:
    ```
    compressa-perf measure \\
        --openai_url https://api.qdrant.mil-team.ru/chat-2/v1/ \\
        --serv_api_url "${SERV_API_URL}" \\
        --api_key "${OPENAI_API_KEY}" \\
        --model_name Compressa-Qwen2.5-14B-Instruct \\
        --experiment_name "Generated Prompts Run" \\
        --num_tasks 2 \\
        --num_runners 2 \\
        --report_file experiment \\
        --report_mode pdf \\
        --generate_prompts \\
        --num_prompts 1000 \\
        --prompt_length 5000
    ```

3. List all experiments:
    ```
    compressa-perf list
    ```

4. Generate a report for an experiment:
    ```
    compressa-perf report <EXPERIMENT_ID>
    ```
        """,
        formatter_class=argparse.RawTextHelpFormatter
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
        "--openai_url", type=str, required=True, help="OpenAI-compatible API URL"
    )
    parser_run.add_argument(
        "--serv_api_url", type=str, help="Compressa Platform API URL"
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
        "--prompts_file", type=str, help="Path to the file containing prompts (separated by newlines)"
    )
    parser_run.add_argument(
        "--report_file", type=str, help="Path to the file to save report"
    )
    parser_run.add_argument(
        "--report_mode", type=str, help="Extension of the report file (.md, .csv or .pdf)"
    )
    parser_run.add_argument(
        "--num_tasks", type=int, default=100, help="Number of requests to send"
    )
    parser_run.add_argument(
        "--num_runners", type=int, default=10, help="Number of concurrent runners"
    )
    parser_run.add_argument(
        "--api_key", type=str, required=True, help="API key"
    )
    parser_run.add_argument(
        "--generate_prompts", action="store_true", help="Generate random prompts instead of using a file"
    )
    parser_run.add_argument(
        "--num_prompts", type=int, default=100, help="Number of prompts to generate (if --generate_prompts is used)"
    )
    parser_run.add_argument(
        "--prompt_length", type=int, default=100, help="Length of each generated prompt (if --generate_prompts is used)"
    )
    parser_run.add_argument(
        "--max_tokens", type=int, default=1000, help="Maximum number of tokens for the model to generate"
    )
    parser_run.set_defaults(func=run_experiment_args)

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
    parser_report.set_defaults(func=report_experiment_args)

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
    parser_list.add_argument(
        "--show-parameters",
        action="store_true",
        help="Show all parameters for each experiment"
    )
    parser_list.add_argument(
        "--show-metrics",
        action="store_true",
        help="Show metrics for each experiment"
    )
    parser_list.add_argument(
        "--name-filter",
        type=str,
        help="Filter experiments by substring in the name"
    )
    parser_list.add_argument(
        "--param-filter",
        type=str,
        action="append",
        help="Filter experiments by parameter value (e.g., paramkey=value_substring)"
    )
    parser_list.add_argument(
        "--recompute",
        action="store_true",
        help="Recompute metrics before listing experiments"
    )
    parser_list.add_argument(
        "--csv-file",
        type=str,
        default=None,
        help="Path to the CSV file to save the experiments"
    )
    parser_list.set_defaults(func=list_experiments_args)

    parser_yaml = subparsers.add_parser(
        "measure-from-yaml",
        help="Run experiments from a YAML configuration file",
    )
    parser_yaml.add_argument(
        "yaml_file",
        help="YAML configuration file for experiments",
    )
    parser_yaml.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB_PATH,
        help="Path to the SQLite database",
    )
    parser_yaml.add_argument(
        "--api_key",
        type=str,
        required=False,
        help="OpenAI API key",
    )
    parser_yaml.set_defaults(func=run_experiments_from_yaml_args)

    parser_stress = subparsers.add_parser(
        "stress",
        help="Run a continuous stress test (infinite requests, windowed metrics).",
    )
    parser_stress.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB_PATH,
        help="Path to the SQLite database",
    )
    parser_stress.add_argument(
        "--openai_url", type=str, required=True, help="OpenAI-compatible API URL"
    )
    parser_stress.add_argument(
        "--serv_api_url", type=str, help="Compressa Platform API URL"
    )
    parser_stress.add_argument(
        "--model_name", type=str, required=True, help="Model name"
    )
    parser_stress.add_argument(
        "--experiment_name", type=str, required=True, help="Name of the experiment"
    )
    parser_stress.add_argument(
        "--description", type=str, help="Description of the experiment"
    )
    parser_stress.add_argument(
        "--prompts_file", type=str, help="File containing prompts"
    )
    parser_stress.add_argument(
        "--report_file", type=str, help="Path to the file to save report"
    )
    parser_stress.add_argument(
        "--report_mode", type=str, help="Extension of the report file (.md, .csv or .pdf)"
    )
    parser_stress.add_argument(
        "--num_runners", type=int, default=10, help="Number of concurrent runners"
    )
    parser_stress.add_argument(
        "--api_key", type=str, required=True, help="API key"
    )
    parser_stress.add_argument(
        "--generate_prompts", action="store_true", help="Generate random prompts instead of using a file"
    )
    parser_stress.add_argument(
        "--num_prompts", type=int, default=100, help="Number of prompts to generate (if --generate_prompts)"
    )
    parser_stress.add_argument(
        "--prompt_length", type=int, default=100, help="Length of each generated prompt (if --generate_prompts)"
    )
    parser_stress.add_argument(
        "--max_tokens", type=int, default=1000, help="Maximum tokens for generation"
    )
    parser_stress.add_argument(
        "--report_freq_min", type=float, default=1, help="Frequency (minutes) to compute windowed metrics"
    )

    parser_stress.set_defaults(func=run_continuous_stress_test_args)

    def default_function(args):
        parser.print_help()

    parser.set_defaults(func=default_function)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
