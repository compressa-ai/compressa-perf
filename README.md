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

```bash
compressa-perf run --help
```

```bash
compressa-perf run \
    --openai_url https://api.qdrant.mil-team.ru/chat-2/v1/ \
    --openai_api_key "${OPENAI_API_KEY}" \
    --model_name Compressa-Qwen2.5-14B-Instruct \
    --experiment_name "My First Run" \
    --prompts_file resources/prompts.csv \
    --num_tasks 100 \
    --num_runners 5
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.