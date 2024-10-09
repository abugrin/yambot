import os
import random

from dotenv import load_dotenv
from requests import post, get
load_dotenv()

GPT_COMPLETION_POINT = '/foundationModels/v1/completion'
url = "https://llm.api.cloud.yandex.net"
headers = {
    "Authorization": f"Api-Key {os.getenv('GPT_API_KEY')}",
    "ContentType": "application/json"
}

def send_text_request(text, context: []):
    path = url + GPT_COMPLETION_POINT
    body = {
        'modelUri': f'gpt://{os.getenv('GPT_FOLDER')}/yandexgpt/latest',
        'completionOptions': {
            'stream': False,
            'temperature': 0.6,
            'maxTokens': 2000
        },
    }
    messages = [
        {'role': 'system', 'text': 'Ты умный ассистент'},
        {'role': 'user', 'text': text}
    ]
    for context in context:
        messages.append({'role': 'assistant', 'text': context})
    body.update({'messages' : messages})

    print(f"Text generation request: {body}")

    response = post(path, headers=headers, json=body)

    print(f"Text generation response: {response.json()}")
    return response.json()

def send_translate_request(text):
    path = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    body = {'folderId': os.getenv('GPT_FOLDER'), 'texts': [text], 'targetLanguageCode': 'ru'}
    response = post(path, headers=headers, json=body)

    print(f"Translate response: {response.json()}")
    return response.json()


def send_art_request(text):
    path = url + "/foundationModels/v1/imageGenerationAsync"

    body = {
        'modelUri': f"art://{os.getenv('GPT_FOLDER')}/yandex-art/latest",
        'messages': [
            {
                'text': text,
                'weight': 1
            }
        ],
        'generation_options': {
            'mime_type': 'image/jpeg',
            'seed': random.randint(1, 100)
        }
    }

    response = post(path, json=body, headers=headers)
    return response.json()


def get_art_response(request_id):
    path = url + f"/operations/{request_id}"
    response = get(path, headers=headers)
    return response.json()
