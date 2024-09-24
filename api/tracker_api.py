import os

from requests import post

url = "https://api.tracker.yandex.net"
headers = {
    "Authorization": f"OAuth {os.getenv('TRACKER_KEY')}",
    "ContentType": "application/json",
    "X-Org-ID": os.getenv('TRACKER_ORG')
}


def create_ticket(name):
    path = url + "/v2/issues"
    tracker_queue = os.getenv('TRACKER_QUEUE')

    ticket = {
        'queue': tracker_queue,
        'summary': name
    }

    res = post(path, json=ticket, headers=headers)

    return res.json()
