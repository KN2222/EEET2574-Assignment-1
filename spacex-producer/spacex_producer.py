
import os
import time
import requests
from kafka import KafkaProducer
import json

KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL", "localhost:9092")
TOPIC_NAME = os.environ.get("TOPIC_NAME", "spacex")
SLEEP_TIME = int(os.environ.get("SLEEP_TIME", 60))

API_URL = "https://api.spacexdata.com/v4/launches/upcoming"

def fetch_upcoming_launches():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    return []

def run():
    print(f"Starting SpaceX producer at {KAFKA_BROKER_URL}")
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER_URL],
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
    )

    while True:
        launches = fetch_upcoming_launches()
        for launch in launches:
            print(f"Sending launch data: {launch['name']}")
            producer.send(TOPIC_NAME, value=launch)
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    run()