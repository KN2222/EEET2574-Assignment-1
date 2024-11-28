
from kafka import KafkaConsumer
import os
import json

if __name__ == "__main__":
    print("Starting SpaceX Consumer")
    TOPIC_NAME = os.environ.get("SPACEX_TOPIC_NAME", "spacex")
    KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL", "localhost:9092")

    print(f"Setting up Kafka consumer at {KAFKA_BROKER_URL}")
    consumer = KafkaConsumer(TOPIC_NAME, bootstrap_servers=[KAFKA_BROKER_URL])

    print('Waiting for SpaceX msg...')
    for msg in consumer:
        launch_data = json.loads(msg.value.decode('utf-8'))
        print(f"Consumed launch: {launch_data}")