# Compressa Performance Measurement Tool

This tool is designed to measure the performance of Compressa models.  
It uses the OpenAI API to run inference tasks and stores the results in a SQLite database.

## Installation

```bash
git clone https://github.com/compressa-ai/compressa-perf.git
cd compressa-perf
poetry install
```

## Install with Pip

```bash
pip install compressa-perf
```

## Usage

### 1. Run experiment with prompts from a file

```bash
compressa-perf measure \
    --openai_url https://api.qdrant.mil-team.ru/chat-2/v1/ \
    --openai_api_key "${OPENAI_API_KEY}" \
    --model_name Compressa-Qwen2.5-14B-Instruct \
    --experiment_name "File Prompts Run" \
    --prompts_file resources/prompts.csv \
    --num_tasks 1000 \
    --num_runners 100
```

### 2. Run experiment with generated prompts

```bash
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

### 3. List all experiments

```bash
compressa-perf list
```

Output example:
```
╘═══════════════════════╧══════════╛
❯ compressa-perf list

List of Experiments:
+------+------------------+---------------------+---------------+
|   ID | Name             | Date                | Description   |
+======+==================+=====================+===============+
|    8 | File Prompts Run | 2024-09-24 07:40:01 |               |
+------+------------------+---------------------+---------------+
|    7 | My First Run     | 2024-09-24 07:31:31 |               |
+------+------------------+---------------------+---------------+
|    6 | My First Run     | 2024-09-24 07:29:18 |               |
+------+------------------+---------------------+---------------+
|    5 | My First Run     | 2024-09-24 07:28:39 |               |
+------+------------------+---------------------+---------------+
|    4 | My First Run     | 2024-09-24 07:27:36 |               |
+------+------------------+---------------------+---------------+
|    3 | My First Run     | 2024-09-24 07:10:39 |               |
+------+------------------+---------------------+---------------+
|    2 | My First Run     | 2024-09-24 07:10:06 |               |
+------+------------------+---------------------+---------------+
|    1 | My First Run     | 2024-09-24 07:09:48 |               |
+------+------------------+---------------------+---------------+
```

### 4. Generate a report for an experiment

```bash
compressa-perf report <EXPERIMENT_ID>
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
│   openai_url │ https://api.qdrant.mil-team.ru/chat-2/v1/ │
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
╒═══════════════════════╤══════════╕
│ Metric                │    Value │
╞═══════════════════════╪══════════╡
│ MetricName.TTFT       │   0.7753 │
├───────────────────────┼──────────┤
│ MetricName.LATENCY    │   7.5016 │
├───────────────────────┼──────────┤
│ MetricName.TPOT       │   0.01   │
├───────────────────────┼──────────┤
│ MetricName.THROUGHPUT │ 207.84   │
╘═══════════════════════╧══════════╛
```

For more information on available commands and options, run:

```bash
compressa-perf --help
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
