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
    check_balances,
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
    # node_url is always required - either for direct connection or testnet account creation
    if not args.node_url:
        raise ValueError("--node_url is required")
    
    run_experiment(
        db=args.db,
        node_url=args.node_url,
        model_name=args.model_name,
        account_address=args.account_address,
        private_key_hex=args.private_key_hex,
        experiment_name=args.experiment_name,
        description=args.description,
        prompts_file=args.prompts_file,
        num_tasks=args.num_tasks,
        num_runners=args.num_runners,
        generate_prompts=args.generate_prompts,
        num_prompts=args.num_prompts,
        prompt_length=args.prompt_length,
        max_tokens=args.max_tokens,
        no_sign=args.no_sign,
        old_sign=args.old_sign,
        create_account_testnet=args.create_account_testnet,
        account_name=args.account_name,
        inferenced_path=args.inferenced_path
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
        node_url=args.node_url,
        account_address=args.account_address,
        private_key_hex=args.private_key_hex,
        model_name=args.model_name,
        no_sign=args.no_sign,
        old_sign=args.old_sign,
        create_account_testnet=args.create_account_testnet,
        account_name=args.account_name,
        inferenced_path=args.inferenced_path
    )


def run_continuous_stress_test_args(args):
    # node_url is always required - either for direct connection or testnet account creation
    if not args.node_url:
        raise ValueError("--node_url is required")
    
    run_continuous_stress_test(
        db=args.db,
        node_url=args.node_url,
        model_name=args.model_name,
        account_address=args.account_address,
        private_key_hex=args.private_key_hex,
        experiment_name=args.experiment_name,
        description=args.description,
        prompts_file=args.prompts_file,
        num_runners=args.num_runners,
        generate_prompts=args.generate_prompts,
        num_prompts=args.num_prompts,
        prompt_length=args.prompt_length,
        max_tokens=args.max_tokens,
        report_freq_min=args.report_freq_min,
        no_sign=args.no_sign,
        old_sign=args.old_sign,
        create_account_testnet=args.create_account_testnet,
        account_name=args.account_name,
        inferenced_path=args.inferenced_path
    )


def check_balances_args(args):
    check_balances(
        node_url=args.node_url,
    )



def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for running and analyzing experiments",
        epilog="""
Examples:
1. Run experiment with prompts from a file:
    ```
    compressa-perf measure \\
        --node_url http://example.node.url:8545 \\
        --model_name Qwen/Qwen2.5-7B-Instruct \\
        --account_address 0x1234567890abcdef1234567890abcdef12345678 \\
        --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \\
        --experiment_name "File Prompts Run" \\
        --prompts_file resources/prompts.csv \\
        --num_tasks 1000 \\
        --num_runners 100
    ```
2. Run experiment with generated prompts:
    ```
    compressa-perf measure \\
        --node_url http://example.node.url:8545 \\
        --model_name Qwen/Qwen2.5-7B-Instruct \\
        --account_address 0x1234567890abcdef1234567890abcdef12345678 \\
        --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \\
        --experiment_name "Generated Prompts Run" \\
        --num_tasks 2 \\
        --num_runners 2 \\
        --generate_prompts \\
        --num_prompts 1000 \\
        --prompt_length 5000
    ```

3. Run experiments from a YAML configuration file:
    ```
    compressa-perf measure-from-yaml \\
        --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \\
        config.yml
    ```

4. Run experiments from a YAML configuration file with overridden node_url:
    ```
    compressa-perf measure-from-yaml \\
        --node_url http://override.node.url:8545 \\
        --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \\
        config.yml
    ```

5. Run experiments from a YAML configuration file with overridden model_name:
    ```
    compressa-perf measure-from-yaml \\
        --model_name Qwen/Qwen2.5-14B-Instruct \\
        --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \\
        config.yml
    ```

6. Run experiments from a YAML configuration file with overridden account_address:
    ```
    compressa-perf measure-from-yaml \\
        --account_address 0x9876543210abcdef9876543210abcdef98765432 \\
        --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \\
        config.yml
    ```

7. List all experiments:
    ```
    compressa-perf list
    ```

8. Generate a report for an experiment:
    ```
    compressa-perf report <EXPERIMENT_ID>
    ```
        """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command')

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
        "--node_url", type=str, required=True, help="Node URL (used for blockchain connection and testnet account creation)"
    )
    parser_run.add_argument(
        "--model_name", type=str, required=True, help="Model name"
    )
    parser_run.add_argument(
        "--account_address", type=str, required=False, help="Account address"
    )
    parser_run.add_argument(
        "--private_key_hex", type=str, required=False, help="Private key hex"
    )
    parser_run.add_argument(
        "--no-sign", action="store_true", help="Send requests without signing"
    )
    parser_run.add_argument(
        "--old-sign", action="store_true", help="Use legacy signing method for backward compatibility"
    )
    parser_run.add_argument(
        "--create-account-testnet", action="store_true", help="Automatically create account and export key for testnet using --node_url before running experiment"
    )
    parser_run.add_argument(
        "--account-name", type=str, required=False, help="Account name for testnet account creation (optional if --create-account-testnet)"
    )
    parser_run.add_argument(
        "--inferenced-path", type=str, default="./inferenced", help="Path to the inferenced binary (default: ./inferenced, fallback: inferenced in PATH)"
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
        "--num_tasks", type=int, default=100, help="Number of requests to send"
    )
    parser_run.add_argument(
        "--num_runners", type=int, default=10, help="Number of concurrent runners"
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
        "--node_url",
        type=str,
        required=False,
        help="Node URL (overrides value in config.yml if provided)",
    )
    parser_yaml.add_argument(
        "--account_address",
        type=str,
        required=False,
        help="Account address (overrides value in config.yml if provided)",
    )
    parser_yaml.add_argument(
        "--model_name",
        type=str,
        required=False,
        help="Model name (overrides value in config.yml if provided)",
    )
    parser_yaml.add_argument(
        "--private_key_hex",
        type=str,
        required=False,
        help="Private key hex",
    )
    parser_yaml.add_argument(
        "--no-sign", action="store_true", help="Send requests without signing"
    )
    parser_yaml.add_argument(
        "--old-sign", action="store_true", help="Use legacy signing method for backward compatibility"
    )
    parser_yaml.add_argument(
        "--create-account-testnet", action="store_true", help="Automatically create account and export key for testnet using --node_url before running experiment"
    )
    parser_yaml.add_argument(
        "--account-name", type=str, required=False, help="Account name for testnet account creation (optional if --create-account-testnet)"
    )
    parser_yaml.add_argument(
        "--inferenced-path", type=str, default="./inferenced", help="Path to the inferenced binary (default: ./inferenced, fallback: inferenced in PATH)"
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
        "--node_url", type=str, required=True, help="Node URL (used for blockchain connection and testnet account creation)"
    )
    parser_stress.add_argument(
        "--model_name", type=str, required=True, help="Model name"
    )
    parser_stress.add_argument(
        "--account_address", type=str, required=False, help="Account address"
    )
    parser_stress.add_argument(
        "--private_key_hex", type=str, required=False, help="Private key hex"
    )
    parser_stress.add_argument(
        "--no-sign", action="store_true", help="Send requests without signing"
    )
    parser_stress.add_argument(
        "--old-sign", action="store_true", help="Use legacy signing method for backward compatibility"
    )
    parser_stress.add_argument(
        "--create-account-testnet", action="store_true", help="Automatically create account and export key for testnet using --node_url before running experiment"
    )
    parser_stress.add_argument(
        "--account-name", type=str, required=False, help="Account name for testnet account creation (optional if --create-account-testnet)"
    )
    parser_stress.add_argument(
        "--inferenced-path", type=str, default="./inferenced", help="Path to the inferenced binary (default: ./inferenced, fallback: inferenced in PATH)"
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
        "--num_runners", type=int, default=10, help="Number of concurrent runners"
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

    parser_balances = subparsers.add_parser(
        "check-balances",
        help="Check the balance of the account on the specified node.",
    )
    parser_balances.add_argument(
        "--node_url",
        type=str,
        required=True,
        help="Node URL to check balance on.",
    )
    parser_balances.set_defaults(func=check_balances_args)



    def default_function(args):
        parser.print_help()

    parser.set_defaults(func=default_function)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
