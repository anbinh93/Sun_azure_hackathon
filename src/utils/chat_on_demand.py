import os
import sys
sys.path.append(os.getcwd())  # NOQA

from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2023-05-15"
)


def chat_on_demand(messages: list):
    response = client.chat.completions.create(
        model='gpt-3.5-turbo-1106',
        messages=messages,
        max_tokens=4096,
        temperature=1
    )

    return response.choices[0].message.content
