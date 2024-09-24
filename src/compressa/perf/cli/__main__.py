import argparse
from compressa.perf.cli.tools import (
    run_experiment,
    report_experiment,
    list_experiments,
    DEFAULT_DB_PATH,
)


def run_experiment_args(args):
    run_experiment(
        db=args.db,
        openai_api_key=args.openai_api_key,
        openai_url=args.openai_url,
        model_name=args.model_name,
        experiment_name=args.experiment_name,
        description=args.description,
        prompts_file=args.prompts_file,
        num_tasks=args.num_tasks,
        num_runners=args.num_runners,
        generate_prompts=args.generate_prompts,
        num_prompts=args.num_prompts,
        prompt_length=args.prompt_length
    )


def report_experiment_args(args):
    report_experiment(
        experiment_id=args.experiment_id,
        db=args.db,
        recompute=args.recompute
    )


def list_experiments_args(args):
    list_experiments(db=args.db)


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for running and analyzing experiments",
        epilog="""
Examples:
1. Run experiment with prompts from a file:
    ```
    compressa-perf measure \
        --openai_url https://api.qdrant.mil-team.ru/chat-2/v1/ \
        --openai_api_key "${OPENAI_API_KEY}" \
        --model_name Compressa-Qwen2.5-14B-Instruct \
        --experiment_name "File Prompts Run" \
        --prompts_file resources/prompts.csv \
        --num_tasks 1000 \
        --num_runners 100
    ```
2. Run experiment with generated prompts:
    ```
    compressa-perf measure \
        --openai_url https://api.qdrant.mil-team.ru/chat-2/v1/ \
        --openai_api_key "${OPENAI_API_KEY}" \
        --model_name Compressa-Qwen2.5-14B-Instruct \
        --experiment_name "Generated Prompts Run" \
        --num_tasks 2 \
        --num_runners 2 \
        --generate_prompts \
        --num_prompts 1000 \
        --prompt_length 5000
    ```

3. List all experiments:
    ```
    compressa-perf list
    ```

4. Generate a report for an experiment:
    ```
    compressa-perf report 1
    ```
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        "--prompts_file", type=str, help="Path to the file containing prompts"
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
    parser_run.add_argument(
        "--generate_prompts", action="store_true", help="Generate random prompts instead of using a file"
    )
    parser_run.add_argument(
        "--num_prompts", type=int, default=100, help="Number of prompts to generate (if --generate_prompts is used)"
    )
    parser_run.add_argument(
        "--prompt_length", type=int, default=100, help="Length of each generated prompt (if --generate_prompts is used)"
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
    parser_list.set_defaults(func=list_experiments_args)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
