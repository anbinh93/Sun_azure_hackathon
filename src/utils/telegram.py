import datetime
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_ID = os.getenv('TELEGRAM_ID')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


def send_message(data: dict = None):
    time_now = datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S")

    msg = f'[{time_now}] Dữ liệu khách hàng mới:\n'

    response = requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage', data={
        'chat_id': TELEGRAM_ID,
        'text': msg + json.dumps(data, indent=4, ensure_ascii=False)
    })

    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print(
            f"Failed to send the message. Status code: {response.status_code}")
