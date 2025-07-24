# Compressa Performance Measurement Tool

This tool is designed to measure the performance of Compressa models.  
It uses the OpenAI API to run inference tasks and stores the results in a SQLite database.

## Installation

```bash
git clone https://github.com/compressa-ai/compressa-perf.git
cd compressa-perf
poetry install
$(poetry env activate)
```

## Install with Pip

```bash
pip install compressa-perf
```

## Usage

### 1. Run experiment with prompts from a file

```bash
❯ compressa-perf measure \
    --db some_db.sqlite \
    --openai_url https://some-api-url.ru/ \
    --api_key "${OPENAI_API_KEY}" \
    --model_name Compressa-Qwen2.5-14B-Instruct \
    --experiment_name "File Prompts Run" \
    --prompts_file resources/prompts.csv \
    --num_tasks 1000 \
    --num_runners 100
```

### 2. Run experiment with generated prompts

```bash
❯ compressa-perf measure \
    --db some_db.sqlite \
    --openai_url https://some-api-url.ru/chat-2/v1/ \
    --api_key "${OPENAI_API_KEY}" \
    --model_name Compressa-Qwen2.5-14B-Instruct \
    --experiment_name "Generated Prompts Run" \
    --num_tasks 2 \
    --num_runners 2 \
    --generate_prompts \
    --num_prompts 1000 \
    --prompt_length 5000
```

Full parameter list can be obtained with `compressa-perf measure -h`.

### 3. Run set of experiments from YAML file

You can describe set of experiments in YAML file and run them on different services in one command:

```bash
❯ compressa-perf measure-from-yaml experiments.yaml \
    --db some_db.sqlite \
```

Example of YAML file:

```yaml
- openai_url: http://localhost:5000/v1/
  api_key: ${OPENAI_API_KEY}
  model_name: Compressa-LLM
  experiment_name: "File Prompts Run 1"
  description: "Experiment using prompts from a file with 500 tasks and 5 runners"
  prompts_file: resources/prompts.csv
  num_tasks: 500
  num_runners: 5
  generate_prompts: false
  num_prompts: 0
  prompt_length: 0
  max_tokens: 1000 

- openai_url: https://some-api-url/v1/
  api_key: ${OPENAI_API_KEY}
  model_name: Compressa-LLM
  experiment_name: "File Prompts Run 2"
  description: "Experiment using prompts from a file with 20 tasks and 10 runners"
  prompts_file: resources/prompts.csv
  num_tasks: 20
  num_runners: 10
  generate_prompts: true
  num_prompts: 10
  prompt_length: 10000
  max_tokens: 100
```

**List of Parameters**

- `openai_url` - url to chat completion endpoint - `REQUIRED`
- `serv_api_url` - url to service handlers of the Compressa platform - default is `http://localhost:5100/v1/` (if `None` - the inference only will run)
- `api_key` - API key - `REQUIRED`
- `model_name` - served model name - `REQUIRED`
- `experiment_name` - `REQUIRED`
- `description`
- `prompts_file` - path to the file with prompts
- `report_file` - path to the report file - default is `results/experiment`
- `report_mode` - report file extension (`.csv`, `.md`, `.pdf`) - default is `.pdf`
- `num_tasks`
- `num_runners`
- `generate_prompts` - `true` or `false`
- `num_prompts`
- `prompt_length`
- `max_tokens`

### 4. List experiments

You can select experiments by name, parameters or metrics (or substrings in these fields) via `compressa-perf list` command.

For example:
```
❯ compressa-perf list \
    --show-metrics \
    --param-filter openai_url=chat-2 \
    --param-filter avg_n_input=30

List of Experiments:
+----+----------------------------------------------------------------------------+---------------------+--------+-----------------------+
|    | ID                                                                         | Name                | Date   | Description           |
+====+============================================================================+=====================+========+=======================+
| 25 | Compressa-Qwen2.5-14B-Instruct-Int4 Long Input / Short Output | 5 runners  | 2024-10-03 06:21:45 |        | ttft: 25.0960         |
|    |                                                                            |                     |        | latency: 52.5916      |
|    |                                                                            |                     |        | tpot: 0.5530          |
|    |                                                                            |                     |        | throughput: 2891.0323 |
+----+----------------------------------------------------------------------------+---------------------+--------+-----------------------+
| 23 | Compressa-Qwen2.5-14B-Instruct-Int4 Long Input / Short Output | 4 runners  | 2024-10-03 06:14:57 |        | ttft: 17.1862         |
|    |                                                                            |                     |        | latency: 37.9612      |
|    |                                                                            |                     |        | tpot: 0.3954          |
|    |                                                                            |                     |        | throughput: 3230.8769 |
+----+----------------------------------------------------------------------------+---------------------+--------+-----------------------+
```

Full parameter list:
```bash
❯ compressa-perf list -h
usage: compressa-perf list [-h] [--db DB] [--show-parameters] [--show-metrics] [--name-filter NAME_FILTER] [--param-filter PARAM_FILTER]

options:
  -h, --help            show this help message and exit
  --db DB               Path to the SQLite database
  --show-parameters     Show all parameters for each experiment
  --show-metrics        Show metrics for each experiment
  --name-filter NAME_FILTER
                        Filter experiments by substring in the name
  --param-filter PARAM_FILTER
                        Filter experiments by parameter value (e.g., paramkey=value_substring)
```


### 5. Generate a report for an experiment

In addition to the `.pdf`, `.csv` or `.md` reports the text reports also can be generated with the command:

```bash
❯ compressa-perf report <EXPERIMENT_ID>
```

Output example:

```
❯ compressa-perf report 3

Experiment Details:
ID: 3
Name: My First Run
Date: 2024-09-24 07:10:39
Description: None

Experiment Parameters:
╒══════════════╤═══════════════════════════════════════════╕
│    Parameter │                                     Value │
╞══════════════╪═══════════════════════════════════════════╡
│  num_workers │                                         2 │
├──────────────┼───────────────────────────────────────────┤
│    num_tasks │                                         2 │
├──────────────┼───────────────────────────────────────────┤
│   openai_url │ https://some-api-url.ru/chat-2/v1/        │
├──────────────┼───────────────────────────────────────────┤
│  max_tokens  │                                      1000 │
├──────────────┼───────────────────────────────────────────┤
│  model_name  │                             Compressa-LLM │
├──────────────┼───────────────────────────────────────────┤
│  avg_n_input │                                        32 │
├──────────────┼───────────────────────────────────────────┤
│  std_n_input │                                    2.8284 │
├──────────────┼───────────────────────────────────────────┤
│ avg_n_output │                                  748.5000 │
├──────────────┼───────────────────────────────────────────┤
│ std_n_output │                                    2.1213 │
╘══════════════╧═══════════════════════════════════════════╛

Experiment Metrics:

╒══════════════════════════╤══════════╕
│ Metric                   │    Value │
╞══════════════════════════╪══════════╡
│ TTFT                     │   0.0622 │
├──────────────────────────┼──────────┤
│ TTFT_95                  │   0.0693 │
├──────────────────────────┼──────────┤
│ TOP_5_TTFT               │   0.0757 │
├──────────────────────────┼──────────┤
│ LATENCY                  │   0.4642 │
├──────────────────────────┼──────────┤
│ LATENCY_95               │   0.6452 │
├──────────────────────────┼──────────┤
│ TOP_5_LATENCY            │   0.7156 │
├──────────────────────────┼──────────┤
│ TPOT                     │   0.0265 │
├──────────────────────────┼──────────┤
│ THROUGHPUT               │ 100.162  │
├──────────────────────────┼──────────┤
│ THROUGHPUT_INPUT_TOKENS  │  62.4664 │
├──────────────────────────┼──────────┤
│ THROUGHPUT_OUTPUT_TOKENS │  37.6953 │
├──────────────────────────┼──────────┤
│ RPS                      │   2.154  │
├──────────────────────────┼──────────┤
│ LONGER_THAN_60_LATENCY   │   0      │
├──────────────────────────┼──────────┤
│ LONGER_THAN_120_LATENCY  │   0      │
├──────────────────────────┼──────────┤
│ LONGER_THAN_180_LATENCY  │   0      │
├──────────────────────────┼──────────┤
│ FAILED_REQUESTS          │   0      │
├──────────────────────────┼──────────┤
│ FAILED_REQUESTS_PER_HOUR │   0      │
╘══════════════════════════╧══════════╛

```

For more information on available commands and options, run:

```bash
compressa-perf --help
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
