import os
import requests
import json
from typing import (
    Generator,
    Optional,
    Dict,
    Any,
    List
)
import logging
import logging.handlers
import queue

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


def stream_chat(
    api_key: str,
    api_url: str,
    model: str,
    messages: List[Dict[str, str]],
    **kwargs
) -> Generator[Optional[str], None, None]:

    if api_url.endswith('/'):
        api_url = api_url[:-1]
    api_url = f"{api_url}/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        "model": model,
        "messages": messages,
        "stream": True,
        "stream_options": {
            "include_usage": True
        }
    }
    data.update(kwargs)
    usage_data = {}
    try:
        response = requests.post(api_url, headers=headers, json=data, stream=True)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data:'):
                    data_str = decoded_line[len('data: '):].strip()
                    if data_str == '[DONE]':
                        break
                    try:
                        data_json = json.loads(data_str)
                        if 'error' in data_json:
                            break
                        choices = data_json.get('choices', [])
                        if choices:
                            delta = choices[0].get('delta', {})
                            content = delta.get('content')
                            if content:
                                yield content
                        else:
                            usage_data = data_json.get('usage', {})
                    except json.JSONDecodeError:
                        continue
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    finally:
        response.close()
        yield {'usage': usage_data}


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    log_queue = queue.Queue()

    queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    listener = logging.handlers.QueueListener(log_queue, logging.StreamHandler())
    listener.start()

    return logger