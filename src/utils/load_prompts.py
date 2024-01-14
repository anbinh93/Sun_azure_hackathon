import json
import os
import sys
sys.path.append(os.getcwd())

with open('config/prompts.json', 'r', encoding='utf-8') as f:
    PROMPTS = json.load(f)


def load_prompts(type: str) -> None:
    """
        Load path from json file and read the path (txt file) to get the prompt
    Args:
        type (str)

    Note that path must be start from root directory
    """
    path = PROMPTS[type]

    with open(f'prompts/{path}', 'r', encoding='utf-8') as f:
        prompt = f.read()

    return prompt.strip()
