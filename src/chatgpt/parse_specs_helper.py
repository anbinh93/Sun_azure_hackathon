import json
import os
import sys
import traceback
from datetime import datetime
sys.path.append(os.getcwd())  # NOQA

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI"),
)


def my_exception_hook(exctype, value, tb):
    formatted_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    os.makedirs("logs", exist_ok=True)

    with open("logs/error.log", "a", encoding='utf-8') as f:
        f.write(f"==>> Time: {formatted_time}\n")
        f.write(f"==>> Type: {exctype}\n")
        f.write(f"==>> Value: {value}\n")
        f.write("==>> Traceback:\n")
        traceback.print_tb(tb, file=f)
        f.write("\n")

    print(f"==>> Type: {type}")
    print(f"==>> Value: {value}")
    traceback.print_tb(tb)


sys.excepthook = my_exception_hook


def _tgdd_parser_prompt(raw_specs: str) -> str:
    """
        Provide the raw spec of a laptop, build a prompt to make features more robusts and return as json
    Args:
        raw_specs (str)

    Returns:
        str: The prompt for parsing the product links
    """

    message = f"""Given the raw specs containing of a laptop: {raw_specs}

    Extract the specs of the laptop and return as json object includes:
    {{
        'laptop_type': str, (gaming, workstation, business, normal) (You can infer from the name of the laptop, do not uppercase the first letter)
        'cpu': str, (Keep the name of the cpu as it is in the raw specs)
        'cpu_generation': int, (For example, if the cpu is i7-1165G7, the cpu generation is 11 , and i7 13620H, then it is 13) 
        'disk_type': str,
        'disk_size': int,
        'ram_gb': int,
        'max_ram_slot': int, (If the you can't find this info, set it to 1)
        'screen_size': float,
        'screen_resolution': str, (You have to infer and remove all to get this format: width x height, for example: 1920 x 1080),
        'screen_ratio': str, (You have to infer from the screen_resolution and remove all to get this format: width : height, for example: 16:9 for 1920 x 1080 and 16:10 for 1920 x 1200),
        'screen_refresh_rate': int, (If the you can't find this info, set it to 60)
        'gpu_type': str (dedicated or integrated),
        'gpu_model': str, (you have to add the gpu manufacturer also, nvidia or amd depend on the provided information)
        'weight_kg': float,
        'ports': str, (separated by comma),
        'special_features': str, (separated by comma),
        'release_year': int,
    }}
    
    Remember that the specs of a laptop can be missing, so you need to handle that case.
    Do this process carefully, since it will affect the whole system. Remember that !    
    """

    return message


def convert_json(url: str, raw_specs: str) -> dict:
    """
        Parse the specs of a laptop from the raw html containing the specs of a laptop
    Args:
        raw_specs (str)

    Returns:
        dict: The specs of a laptop
        ```
        {
            'status': 'error',
            'message': str(e),
            'data': None
        }
        ```
    """
    try:
        prompt = _tgdd_parser_prompt(raw_specs)

        # Using gpt-3.5-turbo-instruct
        response = client.chat.completions.create(
            model='gpt-3.5-turbo-1106',
            response_format={
                'type': 'json_object'
            },
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )

        data = response.choices[0].message.content
        with open('data.json', 'w', encoding='utf-8') as f:
            data_dict = json.loads(data)
            json.dump(data_dict, f, indent=4, ensure_ascii=False)

        return {
            'status': 'success',
            'message': f'Successfully parse the specs of {url}',
            'data': data
        }
    except Exception as e:
        print(f'==========> Error when parsing the specs of {url}')
        return {
            'status': 'error',
            'message': str(e),
            'data': None
        }
