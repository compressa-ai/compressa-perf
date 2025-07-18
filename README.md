# Compressa Performance Measurement Tool

This tool is designed to measure the performance of Compressa models.
It uses the OpenAI API to run inference tasks and stores the results in a SQLite database.

## Installation

Install from the repository (recommended for latest features and development):

```bash
git clone https://github.com/compressa-ai/compressa-perf.git
cd compressa-perf
poetry install
```

Or install the latest release from PyPI:

```bash
pip install compressa-perf
```

## Usage

### 1. Run experiment with prompts from a file

```bash
❯ compressa-perf measure \
    --node_url http://example.node.url:8545 \
    --model_name Qwen/Qwen2.5-7B-Instruct \
    --account_address 0x1234567890abcdef1234567890abcdef12345678 \
    --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
    --experiment_name "File Prompts Run" \
    --prompts_file resources/prompts.csv \
    --num_tasks 1000 \
    --num_runners 100 \
    [--no-sign] [--old-sign] [--db path/to/your.sqlite]
```

### 2. Run experiment with generated prompts

```bash
❯ compressa-perf measure \
    --node_url http://example.node.url:8545 \
    --model_name Qwen/Qwen2.5-7B-Instruct \
    --account_address 0x1234567890abcdef1234567890abcdef12345678 \
    --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
    --experiment_name "Generated Prompts Run" \
    --num_tasks 2 \
    --num_runners 2 \
    --generate_prompts \
    --num_prompts 1000 \
    --prompt_length 5000 \
    [--no-sign] [--old-sign] [--db path/to/your.sqlite]
```

### 3. Run experiment with automatic testnet account creation

For testnets, you can automatically create an account and export its private key:

```bash
❯ compressa-perf measure \
    --node_url http://testnet.node.url:8545 \
    --model_name Qwen/Qwen2.5-7B-Instruct \
    --create-account-testnet \
    --account-name "myaccount" \
    --experiment_name "Testnet Run" \
    --num_tasks 10 \
    --num_runners 2 \
    --generate_prompts \
    --num_prompts 100 \
    --prompt_length 1000 \
    [--inferenced-path ./inferenced] [--db path/to/your.sqlite]
```

**Note:** The `--create-account-testnet` option requires the `inferenced` binary to be available either at the path specified by `--inferenced-path` (default: `./inferenced`) or in your system PATH.

Full parameter list can be obtained with `compressa-perf measure -h`.

### 4. Run set of experiments from YAML file

You can describe a set of experiments in a YAML file and run them on different services in one command:

```bash
❯ compressa-perf measure-from-yaml \
    --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
    [--node_url ...] [--account_address ...] [--model_name ...] [--no-sign] [--old-sign] [--db path/to/your.sqlite] \
    config.yml
```

You can override values from the YAML file using command-line options:

```bash
# Override node_url
❯ compressa-perf measure-from-yaml \
    --node_url http://override.node.url:8545 \
    --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
    config.yml

# Override account_address
❯ compressa-perf measure-from-yaml \
    --account_address 0x9876543210abcdef9876543210abcdef98765432 \
    --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
    config.yml

# Override model_name
❯ compressa-perf measure-from-yaml \
    --model_name Qwen/Qwen2.5-14B-Instruct \
    --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
    config.yml

# Use testnet account creation
❯ compressa-perf measure-from-yaml \
    --node_url http://testnet.node.url:8545 \
    --create-account-testnet \
    --account-name "testuser" \
    config.yml
```

Example of YAML file:

```yaml
- model_name: Qwen/Qwen2.5-7B-Instruct
  experiment_name: "File Prompts Run 1"
  description: "Experiment using prompts from a file with 10 tasks and 5 runners"
  prompts_file: resources/prompts.csv
  num_tasks: 10
  num_runners: 5
  generate_prompts: false
  num_prompts: 0
  prompt_length: 0
  max_tokens: 1000
  node_url: "http://example.node.url:8545"
  account_address: "0x1234567890abcdef1234567890abcdef12345678"

- model_name: Qwen/Qwen2.5-7B-Instruct
  experiment_name: "Qwen2-7B Long Input / Short Output"
  description: "Experiment using prompts from a file with 20 tasks and 10 runners"
  prompts_file: resources/prompts.csv
  num_tasks: 20
  num_runners: 10
  generate_prompts: true
  num_prompts: 10
  prompt_length: 10000
  max_tokens: 100
  node_url: "http://example.node.url:8545"
  account_address: "0x1234567890abcdef1234567890abcdef12345678"
```

### 5. Run a continuous stress test (infinite requests, windowed metrics)

> **WIP:** This feature is under active development. Interface and output may change.

```bash
❯ compressa-perf stress \
    --node_url http://example.node.url:8545 \
    --model_name Qwen/Qwen2.5-7B-Instruct \
    --account_address 0x1234567890abcdef1234567890abcdef12345678 \
    --private_key_hex 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
    --experiment_name "Stress Test" \
    --num_runners 10 \
    --report_freq_min 1 \
    [--generate_prompts] \
    [--num_prompts 100] \
    [--prompt_length 100] \
    [--max_tokens 1000] \
    [--description ...] \
    [--prompts_file ...] \
    [--no-sign] \
    [--old-sign] \[--db path/to/your.sqlite]
```

You can also use testnet account creation with the stress test:

```bash
❯ compressa-perf stress \
    --node_url http://testnet.node.url:8545 \
    --model_name Qwen/Qwen2.5-7B-Instruct \
    --create-account-testnet \
    --account-name "stresstest" \
    --experiment_name "Stress Test" \
    --num_runners 10 \
    --report_freq_min 1 \
    --generate_prompts \
    [--inferenced-path ./inferenced] [--db path/to/your.sqlite]
```

Features:
- This command will run an infinite stress test, periodically reporting windowed metrics (TTFT, latency, throughput, etc.)
- Use `Ctrl+C` to stop. Metrics are stored in the database (default: `compressa-perf-db.sqlite`)
- Full parameter list: `compressa-perf stress -h`

### 6. Check account balance on a node

```bash
❯ compressa-perf check-balances --node_url http://36.189.234.237:19252
```

Example output:

```
Node URL: http://36.189.234.237:19252

| Inference URL               |   Weight | Models                   |    Balance | Address                                      |
|-----------------------------|----------|--------------------------|------------|----------------------------------------------|
| http://36.189.234.237:19256 |      148 | Qwen/Qwen2.5-7B-Instruct | 2768338825 | gonka1htdxdu330utqqzsr0a6d7anskd6vcrdjjqkjj8 |
| http://36.189.234.237:19252 |      148 | Qwen/Qwen2.5-7B-Instruct |          0 | gonka1ut2jmw0wz7gz08xydglj9s8zllr05cnlvx2x35 |
| http://36.189.234.237:19250 |      137 | Qwen/Qwen2.5-7B-Instruct | 4745195858 | gonka1r3dyajzcagmfgqsny9kazuhjqvqrj4x484xflp |
| http://36.189.234.237:19254 |      118 | Qwen/Qwen2.5-7B-Instruct | 2800798054 | gonka1xrqrkzr4ypgk3rdrdmwp5xyxmx30t5mzz6dctk |
```

This command checks the balance of the account on the specified node.

### 7. List experiments

You can select experiments by name, parameters, or metrics (or substrings in these fields) via `compressa-perf list` command.

For example:

```bash
❯ compressa-perf list \
    --show-metrics \
    --param-filter node_url=example \
    --param-filter avg_n_input=30
```

You can also recompute all metrics before listing:

```bash
❯ compressa-perf list \
    --recompute \
    --show-metrics \
    --name-filter "Stress Test"
```

Export experiment data to CSV:

```bash
❯ compressa-perf list \
    --show-parameters \
    --show-metrics \
    --csv-file experiments.csv
```

Example output:

```
List of Experiments:
+----+-------------------------------------------------------------------+---------------------+--------+----------------------+
| ID | Name                                                              | Date                | Status | Metrics              |
+====+===================================================================+=====================+========+======================+
| 25 | Compressa-Qwen2.5-14B-Instruct-Int4 Long Input / Short Output     | 2024-10-03 06:21:45 |        | ttft: 25.0960        |
|    | 5 runners                                                         |                     |        | latency: 52.5916     |
|    |                                                                   |                     |        | tpot: 0.5530         |
|    |                                                                   |                     |        | throughput: 2891.03  |
+----+-------------------------------------------------------------------+---------------------+--------+----------------------+
| 23 | Compressa-Qwen2.5-14B-Instruct-Int4 Long Input / Short Output     | 2024-10-03 06:14:57 |        | ttft: 17.1862        |
|    | 4 runners                                                         |                     |        | latency: 37.9612     |
|    |                                                                   |                     |        | tpot: 0.3954         |
|    |                                                                   |                     |        | throughput: 3230.88  |
+----+-------------------------------------------------------------------+---------------------+--------+----------------------+
```

Full parameter list:

```bash
❯ compressa-perf list -h
usage: compressa-perf list [-h] [--db DB] [--show-parameters] [--show-metrics] [--name-filter NAME_FILTER] [--param-filter PARAM_FILTER] [--recompute] [--csv-file CSV_FILE]

options:
  -h, --help            show this help message and exit
  --db DB               Path to the SQLite database (default: compressa-perf-db.sqlite)
  --show-parameters     Show all parameters for each experiment
  --show-metrics        Show metrics for each experiment
  --name-filter NAME_FILTER
                        Filter experiments by substring in the name
  --param-filter PARAM_FILTER
                        Filter experiments by parameter value (e.g., paramkey=value_substring)
  --recompute           Recompute metrics before listing experiments
  --csv-file CSV_FILE   Path to the CSV file to save the experiments
```

### 8. Generate a report for an experiment

```bash
❯ compressa-perf report <EXPERIMENT_ID> [--db path/to/your.sqlite] [--recompute]
```

The `--recompute` option will recalculate all metrics for the experiment before generating the report:

```bash
❯ compressa-perf report 3 --recompute
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
│    node_url  │ http://example.node.url:8545              │
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

## Command-line Options

### Common Options

- `--db`: Path to the SQLite database (default: `compressa-perf-db.sqlite`)
- `--no-sign`: Send requests without signing (for unsigned mode)
- `--old-sign`: Use legacy signing method for backward compatibility
- `--inferenced-path`: Path to the inferenced binary (default: `./inferenced`, fallback: `inferenced` in PATH)

### Testnet Account Creation

- `--create-account-testnet`: Automatically create account and export key for testnet using `--node_url`
- `--account-name`: Account name for testnet account creation (optional, defaults to "testnetuser")

When using `--create-account-testnet`, the tool will:

1. Create a new account on the testnet using the `inferenced` binary
2. Export the private key for the account
3. Use the created account address and private key for the experiment

This is particularly useful for testnets where you need fresh accounts for testing.

For more information on available commands and options, run:

```bash
compressa-perf --help
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

