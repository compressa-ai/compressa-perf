import sqlite3
from tabulate import tabulate
from typing import List
import time
import requests
import uuid
import pandas as pd
import os
from compressa.perf.experiment.inference import ExperimentRunner
from compressa.perf.experiment.analysis import Analyzer
from compressa.perf.data.models import Experiment
from compressa.perf.db.operations import (
    fetch_metrics_by_experiment,
    fetch_parameters_by_experiment,
    fetch_experiment_by_id,
    fetch_all_experiments,
    clear_metrics_by_experiment,
)
from compressa.perf.db.db_inserts import direct_insert_experiment as insert_experiment
from compressa.perf.db.setup import (
    create_tables,
    start_db_writer,
    stop_db_writer,
    get_db_writer,
)
from compressa.perf.cli.pdf_tools import report_to_pdf
import datetime
import sys
import random
import string
from compressa.perf.experiment.config import (
    load_yaml_configs,
)

from compressa.perf.experiment.continuous_stress import ContinuousStressTestRunner

from compressa.utils import get_logger


DEFAULT_DB_PATH = "compressa-perf-db.sqlite"

logger = get_logger(__name__)


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


def generate_random_text(
    length: int,
    choise_generator: random.Random,
):
    date_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    words = [date_string]
    current_length = len(date_string)
    while current_length < length:
        word_length = choise_generator.randint(1, 20)
        word = ''.join(choise_generator.choice(string.ascii_lowercase) for _ in range(word_length))
        words.append(word)
        current_length += len(word) + 1
    
    words.append(". Repeat this text at least 10 times. Number the repetitions.")
    return ' '.join(words)[:length]

def generate_prompts_list(
    num_prompts: int,
    prompt_length: int,
    seed: int = 42,
):
    logger.info(f"Generating {num_prompts} prompts with length {prompt_length} and seed {seed}")
    choise_generator = random.Random(seed)
    prompts = []
    for i in range(num_prompts):
        random_text = generate_random_text(prompt_length - len(str(i)) - 1, choise_generator)
        prompt = f"{i} {random_text}"
        prompts.append(prompt)
    return prompts

def read_prompts_from_file(file_path, prompt_length):
    df = pd.read_csv(file_path, header=None)
    return df[0].map(lambda x: x[:prompt_length]).tolist()


def wait_writer(db_writer, max_timeout=None, timeout=10.0):
    start = time.time()
    while True:
        done = db_writer.wait_for_write(timeout=timeout)
        if done:
            print("All results saved to database.")
            return True
        print("Waiting for saving to database...")

        if max_timeout is not None and (time.time() - start) > max_timeout:
            raise Exception("Saving to database failed")
            return False


def save_report(parameters, _result: dict, model_params: dict, hw_params: dict, report_path: str, report_mode: str) -> str:
    if not os.path.exists("results"):
        os.makedirs("results")
    result = {k: round(v, 3) for k, v in zip(_result.keys(), _result.values())}
    date = datetime.datetime.today().strftime('%d.%m.%Y')
    unique_id = str(uuid.uuid4())[:8]
    exp_df = pd.DataFrame.from_dict(parameters, orient='index').reset_index()
    model_data =  {**model_params, **hw_params}
    model_df = pd.DataFrame.from_dict(model_data, orient='index').reset_index()
    result_df = pd.DataFrame.from_dict(result, orient='index').reset_index()
    result_df.columns = ["Metric", "Value"]
    model_df.columns = ["Model Parameter", "Value"]
    exp_df.columns = ["Experiment Parameter", "Value"]
    if report_mode == "csv":
        model_df.to_csv(f"{report_path}_model_info_{date}_{unique_id}.{report_mode}", index=False)
        result_df.to_csv(f"{report_path}_metrics_{date}_{unique_id}.{report_mode}", index=False)
        exp_df.to_csv(f"{report_path}_experiment_parameters_{date}_{unique_id}.{report_mode}", index=False)
    elif report_mode == "md":
        md_parts = [
            model_df.to_markdown(tablefmt="grid"),
            result_df.to_markdown(tablefmt="grid"),
            exp_df.to_markdown(tablefmt="grid")
            ]
        with open(f"{report_path}_experiment_parameters_{date}_{unique_id}.{report_mode}", 'w') as md:
            md.write("\n\n".join(md_parts))
    else:
        report_to_pdf([model_df, exp_df, result_df], f"{report_path}_{date}_{unique_id}.{report_mode}")
    logger.info(f"Experiment results saved to {report_path}_{date}_{unique_id}.{report_mode} file")
    return report_path

def get_model_info(url: str) -> dict:
    result = {}
    r = requests.get(f"{url}models")
    if r.status_code != 200:
        logger.error(f"Model params request failed - {r.status_code}")
        return {}
    data = r.json()["data"][0]
    result["MODEL"] = data["id"]
    result["ENGINE"] = data.get("owned_by", "")
    result["MAX_MODEL_LENGTH"] = data.get("max_model_len", "")
    return result

def get_hw_info(url: str) -> dict:
    if not url:
        logger.warning(f"No Compressa Platform API provided... Trying defaut API...")
        url = "http://localhost:5100/v1/"
    try:
        r = requests.get(f"{url}gpu_info")
    except:
        logger.error(f"Hardware params request failed")
        return {"DRIVER VERSION": "unknown",
                           "CUDA VERSION": "unknown",
                           "HARDWARE": "unknown",}
    if r.status_code != 200:
        logger.error(f"Hardware params request failed - {r.status_code}")
        return {"DRIVER VERSION": "unknown",
                           "CUDA VERSION": "unknown",
                           "HARDWARE": "unknown",
                }
    data = r.json()
    return data

def run_experiment(
    db: str = DEFAULT_DB_PATH,
    api_key: str = None,
    openai_url: str = None,
    serv_api_url: str = None,
    model_name: str = None,
    experiment_name: str = None,
    description: str = None,
    prompts_file: str = None,
    report_file: str = None,
    report_mode: str = "pdf",
    num_tasks: int = 100,
    num_runners: int = 10,
    generate_prompts: bool = False,
    num_prompts: int = 100,
    prompt_length: int = 100,
    max_tokens: int = 1000,
    seed: int = 42,
):
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    if not report_mode:
        report_mode = "pdf"
        logger.warning(f"Default report mode - .pdf")
    if report_mode not in ["pdf", "md", "csv"]:
        raise ValueError("Unknown report mode")
    if not report_file:
        report_file = "results/experiment_report"
        logger.warning(f"Default report file name - results/experiment_report")

    with sqlite3.connect(db) as conn:
        create_tables(conn)
        start_db_writer(db)
        db_writer = get_db_writer()

        experiment_runner = ExperimentRunner(
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
            prompts = generate_prompts_list(num_prompts, prompt_length, seed)
        else:
            prompts = read_prompts_from_file(prompts_file, prompt_length)

        logger.info(f"Num of prompts: {len(prompts)}\nNum of tasks: {num_tasks}\nNum of runners: {num_runners}\nMax tokens: {max_tokens}")

        experiment_runner.run_experiment(
            experiment_id=experiment.id,
            prompts=prompts,
            num_tasks=num_tasks,
            max_tokens=max_tokens,
            seed=seed,
        )

        wait_writer(db_writer)
        
        analyzer = Analyzer(conn)
        metrics, _io_stats = analyzer.compute_metrics(experiment.id)
        _parameters = {
            "NUM_WORKERS": num_runners,
            "NUM_TASKS": num_tasks,
            "MAX_TOKENS": max_tokens,
        }
        io_stats = {k.upper(): round(v, 2) for k, v in zip(_io_stats.keys(), _io_stats.values())}
        parameters = {**_parameters, **io_stats}
        hw_info = get_hw_info(serv_api_url)
        hw_info["OPENAI_URL"] = openai_url
        model_info = get_model_info(openai_url)
        saved_report = save_report(parameters, metrics, model_info, hw_info, report_file, report_mode)
        db_writer.wait_for_write()
        


    report_experiment(
        experiment_id=experiment.id,
        db=db,
        recompute=False
    )

    stop_db_writer()


def report_experiment(
    experiment_id: int,
    db: str = DEFAULT_DB_PATH,
    recompute: bool = False,
):
    with sqlite3.connect(db) as conn:
        ensure_db_initialized(conn)
        start_db_writer(db)
        db_writer = get_db_writer()
        experiment = fetch_experiment_by_id(conn, experiment_id)
        if not experiment:
            logger.error(f"Error: Experiment with ID {experiment_id} not found.")
            sys.exit(1)

        analyzer = Analyzer(conn)
        
        if recompute:
            clear_metrics_by_experiment(conn, experiment_id)
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
        db_writer.wait_for_write()
        stop_db_writer()


def list_experiments(
    db: str = DEFAULT_DB_PATH,
    show_parameters: bool = False,
    show_metrics: bool = False,
    name_filter: str = None,
    param_filters: str = None,
    recompute: bool = False,
    csv_file: str = None,
):
    with sqlite3.connect(db) as conn:
        ensure_db_initialized(conn)

        experiments = fetch_all_experiments(conn)
        if recompute:
            start_db_writer(db)
            analyzer = Analyzer(conn)
            for exp in experiments:
                try:
                    clear_metrics_by_experiment(conn, exp.id)
                    analyzer.compute_metrics(exp.id)
                except Exception as e:
                    logger.error(f"Error computing metrics for experiment {exp.id}: {e}")
                finally:
                    logger.info(f"Metrics computed for experiment {exp.id}")
        
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

        _print_experiments_cli(
            experiments=experiments,
            conn=conn,
            show_parameters=show_parameters,
            show_metrics=show_metrics,
        )
        if csv_file is not None:
            _export_experiments_csv(
                experiments=experiments,
                conn=conn,
                csv_file=csv_file,
            )


def _print_experiments_cli(
    experiments: List[Experiment],
    conn: sqlite3.Connection,
    show_parameters: bool = False,
    show_metrics: bool = False,
):

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
            metrics_str = "\n".join([f"{m.metric_name}: {format_value(m.metric_value)}" for m in metrics])
            row.append(metrics_str)

        table_data.append(row)

    print("\nList of Experiments:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def _export_experiments_csv(
    experiments: List[Experiment],
    conn: sqlite3.Connection,
    csv_file: str,
):
    table_data = []
    metric_columns = set()

    for exp in experiments:
        item = {}
        item["id"] = exp.id
        item["name"] = exp.experiment_name
        item["date"] = exp.experiment_date.strftime("%Y-%m-%d %H:%M:%S") if exp.experiment_date else "N/A"
        item["description"] = exp.description
        item["parameters"] = {}

        parameters = fetch_parameters_by_experiment(conn, exp.id)
        for p in parameters:
            item["parameters"][p.key] = format_value(p.value, precision=2)

        metrics = fetch_metrics_by_experiment(conn, exp.id)
        for m in metrics:
            metric_column = f"M_{m.metric_name}"
            item[metric_column] = format_value(m.metric_value)
            metric_columns.add(metric_column)

        table_data.append(item)

    df = pd.DataFrame(table_data)
    df = df.reindex(columns=["id", "name", "date", "description", "parameters"] + list(metric_columns), fill_value=None)
    df.to_csv(csv_file, index=False)

def run_experiments_from_yaml(
    yaml_file: str,
    db: str = DEFAULT_DB_PATH,
    api_key: str = None,
):
    # if not api_key:
    #     raise ValueError("OPENAI_API_KEY is not set")

    configs = load_yaml_configs(yaml_file)
    experiment_ids = []
    for config in configs:
        experiment_id = run_experiment(
            db=db,
            api_key=config.api_key,
            openai_url=config.openai_url,
            serv_api_url=config.serv_api_url,
            model_name=config.model_name,
            experiment_name=config.experiment_name,
            description=config.description,
            prompts_file=config.prompts_file,
            report_file=config.report_file,
            report_mode=config.report_mode,
            num_tasks=config.num_tasks,
            num_runners=config.num_runners,
            generate_prompts=config.generate_prompts,
            num_prompts=config.num_prompts,
            prompt_length=config.prompt_length,
            max_tokens=config.max_tokens,
            seed=config.seed,
        )
        experiment_ids.append(experiment_id)

    # Report all experiments after completion
    # for experiment_id in experiment_ids:
    #     report_experiment(
    #         experiment_id=experiment_id,
    #         db=db,
    #         recompute=False
    #     )
    
    list_experiments(db=db)



def run_continuous_stress_test(
    db: str,
    api_key: str,
    openai_url: str,
    model_name: str,
    experiment_name: str,
    description: str,
    prompts_file: str,
    num_runners: int,
    generate_prompts: bool,
    num_prompts: int,
    prompt_length: int,
    max_tokens: int,
    report_freq_min: float,
):
    """
    Creates an Experiment, loads or generates prompts, and starts
    an infinite stress test that computes windowed metrics in real time.
    """
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    with sqlite3.connect(db) as conn:
        create_tables(conn)
        start_db_writer(db)
        db_writer = get_db_writer()
        experiment = Experiment(
            id=None,
            experiment_name=experiment_name,
            experiment_date=datetime.datetime.now(),
            description=description,
        )
        experiment.id = insert_experiment(conn, experiment)
        print(f"Continuous Stress Experiment created: {experiment}")

        if generate_prompts:
            prompts = generate_prompts_list(num_prompts, prompt_length)
        else:
            if not prompts_file:
                raise ValueError("You must provide --prompts_file or use --generate_prompts")
            prompts = read_prompts_from_file(prompts_file, prompt_length)

        logger.info(f"Number of prompts: {len(prompts)}")

        runner = ContinuousStressTestRunner(
            db_path=db,
            api_key=api_key,
            openai_url=openai_url,
            model_name=model_name,
            experiment_id=experiment.id,
            prompts=prompts,
            num_runners=num_runners,
            max_tokens=max_tokens,
            report_freq_min=report_freq_min,
        )
        runner.start_test()

        db_writer.wait_for_write()
        stop_db_writer()
