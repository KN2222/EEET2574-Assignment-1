import asyncio
import configparser
import os
import time
from collections import namedtuple
from kafka import KafkaProducer
from faker import Faker
import json

KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
TOPIC_NAME = os.environ.get("TOPIC_NAME")
SLEEP_TIME = int(os.environ.get("SLEEP_TIME", 5))

fake = Faker()

def get_registered_user():
    return {
        "name": fake.name(),
        "address": fake.address(),
        "year": fake.year(),
        "email": fake.email(),
        "phone_number": fake.phone_number(),
        "company": fake.company(),
        "job": fake.job(),
        "city": fake.city(),
        "country": fake.country(),
        "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=90).strftime("%Y-%m-%d")
    }

def run():
    iterator = 0
    print("Setting up Faker producer at {}".format(KAFKA_BROKER_URL))
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER_URL],
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
    )

    while True:
        sendit = get_registered_user()
        print("Sending new faker data iteration - {}".format(iterator))
        producer.send(TOPIC_NAME, value=sendit)
        print("New faker data sent")
        time.sleep(SLEEP_TIME)
        print("Waking up!")
        iterator += 1


if __name__ == "__main__":
    run()
