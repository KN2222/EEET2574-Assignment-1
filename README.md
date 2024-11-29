# Distributed Big Data Pipeline with Kafka, Cassandra, and Jupyter Lab Using Docker

## Tran Ngoc Khang (S3927201)

Course: EEET2574 | Big Data for Engineering<br>
Assignment 1: Data Pipeline with Docker

### Overview

This guide demonstrates how to build a distributed big data pipeline using Kafka , Cassandra, and Jupyter Lab within Docker containers. The setup is designed to integrate multiple APIs like OpenWeatherMap, Faker, and SpaceX APIs to process and analyze data.

### Presented Video

https://youtu.be/ClpipMmyzYY

### Public Github repo link

https://github.com/KN2222/EEET2574-Assignment-1

### Prerequisites

- Docker installed on your local machine.
- API keys for OpenWeatherMap. [Open Weather Map](https://openweathermap.org/api)
  <br>
- API for SpaceX launches can be access here [SpaceX-API](https://github.com/r-spacex/SpaceX-API)
  <br>
  (Sample keys are provided, but they may be rate-limited if overused.)

## Task 1: Build the Pipeline with OpenWeatherMap and Twitter APIs

### Step 1: Setting Up Docker Networks

```bash
docker network create kafka-network   # Network for Kafka cluster
docker network create cassandra-network  # Network for Cassandra
```

### Step 2: Deploy Cassandra

Cassandra runs keyspace and schema creation scripts automatically.

```bash
docker-compose -f cassandra/docker-compose.yml up -d
```

### Step 3: Deploy Kafka

```bash
docker-compose -f kafka/docker-compose.yml up -d
docker ps -a  # Check Kafka, Zookeeper, Kafka-Manager, and Connect services
```

Kafka-Manager is accessible at:
http://localhost:9000

### Step 4: Start Producers

OpenWeatherMap Producer

```bash
docker-compose -f owm-producer/docker-compose.yml up -d
```

Twitter Classifier + Weather Consumer
Build and start the consumers:

```bash
cd consumers
docker build -t twitterconsumer .
cd ..
docker-compose -f consumers/docker-compose.yml up
```

### Step 5: Verify Cassandra Data Ingestion

Login to the Cassandra container:

```bash
docker exec -it cassandra bash
```

Access cqlsh:

```bash
cqlsh --cqlversion=3.4.4 127.0.0.1
USE kafkapipeline;
SELECT * FROM weatherreport;
```

### Step 6: Visualization with Jupyter Lab

Run the following to visualize data at http://localhost:8888:

```bash
docker-compose -f data-vis/docker-compose.yml up -d
```

## Task 2: Integrate Faker API

### Step 1: Update Cassandra Schema

Create cassandra/schema-faker.cql:

```sql
USE kafkapipeline;

CREATE TABLE IF NOT EXISTS fakerdata (
  name TEXT,
  address TEXT,
  year INT,
  email TEXT,
  phone_number TEXT,
  company TEXT,
  job TEXT,
  city TEXT,
  country TEXT,
  date_of_birth TEXT,
  PRIMARY KEY (name, address)
);
```

Run the schema:

```bash
docker-compose -f cassandra/docker-compose.yml up -d --build
cqlsh -f schema-faker.cql
```

### Step 2: Configure Kafka Connect

Create connect/create-cassandra-sink.sh:

```bash
curl -s -X POST http://localhost:8083/connectors \
-H "Content-Type: application/json" \
-d '{
  "name": "fakersink",
  "config": {
    "connector.class": "com.datastax.oss.kafka.sink.CassandraSinkConnector",
    "topics": "faker",
    "contactPoints": "cassandradb",
    "loadBalancing.localDc": "datacenter1",
    "topic.faker.kafkapipeline.fakerdata.mapping": "name=value.name, address=value.address, year=value.year, email=value.email, phone_number=value.phone_number, company=value.company, job=value.job, city=value.city, country=value.country, date_of_birth=value.date_of_birth",
    "tasks.max": "10"
  }
}'
```

Rebuild Kafka:

```bash
docker-compose -f kafka/docker-compose.yml up -d --build
```

### Step 3: Faker Producer Setup

Modify the copied folder faker-producer with the following Python code (faker_producer.py):

```python
from kafka import KafkaProducer
from faker import Faker
import os, time, json

fake = Faker()
KAFKA_BROKER_URL = os.environ["KAFKA_BROKER_URL"]
TOPIC_NAME = os.environ["TOPIC_NAME"]

def get_registered_user():
    return {
        "name": fake.name(),
        "address": fake.address(),
        "year": fake.year(),
        "email": fake.email(),
        "phone_number": fake.phone_number()
    }

def run():
    producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER_URL], value_serializer=lambda x: json.dumps(x).encode('utf-8'))
    while True:
        producer.send(TOPIC_NAME, value=get_registered_user())
        time.sleep(5)

if __name__ == "__main__":
    run()
```

Build and run the producer:

```bash
docker-compose -f faker-producer/docker-compose.yml up -d
```

### Step 4: Setup Consumers

Add faker_consumer.py in the consumers/python folder:

```python
from kafka import KafkaConsumer
import os, json

consumer = KafkaConsumer("faker", bootstrap_servers=[os.environ["KAFKA_BROKER_URL"]])
for message in consumer:
    print(f"Received: {message.value.decode()}")
```

Update consumers/docker-compose.yml and rebuild:

```bash
docker-compose -f consumers/docker-compose.yml up --build
```

## Task 3: Integrating SpaceX Launch Data API

API Selection: SpaceX Launch Data
The SpaceX API provides live and historical data on launches, rockets, payloads, and more. It is an excellent real-world data source that showcases aerospace innovation and makes the data pipeline more dynamic.

### Step 1: Update Cassandra Schema

We'll store SpaceX launch data in a new Cassandra table.

Create a file cassandra/schema-spacex.cql with the following schema:

```sql
USE kafkapipeline;

CREATE TABLE IF NOT EXISTS spacex_launches (
  launch_id TEXT PRIMARY KEY,
  mission_name TEXT,
  launch_date_utc TIMESTAMP,
  rocket_name TEXT,
  launch_success BOOLEAN,
  site_name TEXT,
  payload_type TEXT,
  payload_mass_kg DOUBLE
);
```

Rebuild and Apply the Schema
Add this file to Cassandra's Dockerfile with the COPY line:

Rebuild and apply the schema:

```bash
docker-compose -f cassandra/docker-compose.yml up -d --build
cqlsh -f schema-spacex.cql

```

### Step 2: Set Up Kafka Connect for SpaceX Data

Create a script kafka/connect/create-spacex-sink.sh to configure a Kafka sink for Cassandra:

```bash
echo "Starting SpaceX Sink"
curl -s \
  -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "spacexsink",
    "config": {
      "connector.class": "com.datastax.oss.kafka.sink.CassandraSinkConnector",
      "value.converter": "org.apache.kafka.connect.json.JsonConverter",
      "key.converter": "org.apache.kafka.connect.json.JsonConverter",
      "value.converter.schemas.enable": "false",
      "key.converter.schemas.enable": "false",
      "tasks.max": "10",
      "topics": "spacex",
      "contactPoints": "cassandradb",
      "loadBalancing.localDc": "datacenter1",
      "topic.spacex.kafkapipeline.spacex_launches.mapping": "launch_id=value.id, mission_name=value.name, launch_date_utc=value.date_utc, rocket_name=value.rocket, launch_success=value.success, site_name=value.launchpad, payload_type=value.payloads[0].type, payload_mass_kg=value.payloads[0].mass_kg"
    }
    }'
echo "Done."
```

### Step 3: Create SpaceX Data Producer

Setup SpaceX Producer
Duplicate the faker-producer folder and rename it to spacex-producer.
Replace the faker_producer.py with the following spacex_producer.py:

```python
import os
import time
import requests
from kafka import KafkaProducer
import json

API_URL = "https://api.spacexdata.com/v4/launches/upcoming"
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "broker:9092")
TOPIC_NAME = os.getenv("TOPIC_NAME", "spacex")

def fetch_launch_data():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()
    return []

def run():
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER_URL],
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    while True:
        launches = fetch_launch_data()
        for launch in launches:
            producer.send(TOPIC_NAME, value=launch)
            print(f"Sent: {launch['name']}")
        time.sleep(300)

if __name__ == "__main__":
    run()

```

Update Dockerfile

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY spacex_producer.py .
RUN pip install kafka-python requests
CMD ["python", "spacex_producer.py"]
```

Rebuild:

```bash
docker-compose -f spacex-producer/docker-compose.yml up -d --build
```

### Step 4: Create SpaceX Consumer

Copy faker_consumer.py to spacex_consumer.py:

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer("spacex", bootstrap_servers=["broker:9092"])
print("Waiting for SpaceX launch data...")
for msg in consumer:
    print(json.loads(msg.value))
```

Update docker-compose.yml with:

```yaml
spacexconsumer:
  image: spacexconsumer
  environment:
    KAFKA_BROKER_URL: broker:9092
    TOPIC_NAME: spacex
  command: ['python', 'spacex_consumer.py']
```

Rebuild and start:

```bash
docker-compose -f consumers/docker-compose.yml up --build -d
```

Step 5: Update Visualization Pipeline
Modify data-vis/docker-compose.yml to include:

```yaml
environment:
  SPACEX_TABLE: spacex_launches
```

Update cassandrautils.py to query spacex_launches.
Here is what the file should look like at the end

```python
import os
import sys
import pandas as pd
from cassandra.cluster import BatchStatement, Cluster, ConsistencyLevel
from cassandra.query import dict_factory

# Configuration
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "kafkapipeline")

# Tables
WEATHER_TABLE = os.getenv("WEATHER_TABLE", "weather")
TWITTER_TABLE = os.getenv("TWITTER_TABLE", "twitter")
SPACEX_TABLE = os.getenv("SPACEX_TABLE", "spacex_launches")
FAKER_TABLE = os.getenv("FAKER_TABLE", "faker_data")

# Insert Data Functions
def saveData(dfrecords, table_name, columns):
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect(CASSANDRA_KEYSPACE)
    session.row_factory = dict_factory

    cqlsentence = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
    insert = session.prepare(cqlsentence)

    batch = BatchStatement(consistency_level=ConsistencyLevel.QUORUM)
    counter = 0
    total_count = 0
    batches = []

    for _, row in dfrecords.iterrows():
        batch.add(insert, tuple(row[col] for col in columns))
        counter += 1
        if counter >= 100:
            print(f'Inserting {counter} records into {table_name}')
            total_count += counter
            counter = 0
            batches.append(batch)
            batch = BatchStatement(consistency_level=ConsistencyLevel.QUORUM)
    if counter != 0:
        batches.append(batch)
        total_count += counter

    [session.execute(b) for b in batches]
    print(f'Inserted {total_count} rows into {table_name}')

def saveTwitterDf(dfrecords):
    columns = ['datetime', 'location', 'tweet', 'classification']
    saveData(dfrecords, TWITTER_TABLE, columns)

def saveWeatherreport(dfrecords):
    columns = ['forecastdate', 'location', 'description', 'temp', 'feels_like', 'temp_min', 'temp_max', 'pressure', 'humidity', 'wind', 'sunrise', 'sunset']
    saveData(dfrecords, WEATHER_TABLE, columns)

def saveSpaceXLaunches(dfrecords):
    columns = ['launch_id', 'mission_name', 'launch_date_utc', 'rocket_name', 'launch_success', 'site_name', 'payload_type', 'payload_mass_kg']
    saveData(dfrecords, SPACEX_TABLE, columns)

def saveFakerData(dfrecords):
    columns = ['name', 'email', 'address', 'phone', 'company']
    saveData(dfrecords, FAKER_TABLE, columns)

# Load and Save Data
def loadDF(targetfile, target):
    if target == 'weather':
        columns = ['description', 'temp', 'feels_like', 'temp_min', 'temp_max', 'pressure', 'humidity', 'wind', 'sunrise', 'sunset', 'location', 'report_time']
        df = pd.read_csv(targetfile, names=columns, parse_dates=['report_time'])
        saveWeatherreport(df)
    elif target == 'twitter':
        columns = ['tweet', 'datetime', 'location', 'classification']
        df = pd.read_csv(targetfile, names=columns, parse_dates=['datetime'])
        saveTwitterDf(df)
    elif target == 'spacex':
        columns = ['launch_id', 'mission_name', 'launch_date_utc', 'rocket_name', 'launch_success', 'site_name', 'payload_type', 'payload_mass_kg']
        df = pd.read_csv(targetfile, names=columns, parse_dates=['launch_date_utc'])
        saveSpaceXLaunches(df)
    elif target == 'faker':
        columns = ['name', 'email', 'address', 'phone', 'company']
        df = pd.read_csv(targetfile, names=columns)
        saveFakerData(df)

# Fetch Data Functions
def getDF(table):
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect(CASSANDRA_KEYSPACE)
    session.row_factory = dict_factory
    cqlquery = f"SELECT * FROM {table};"
    rows = session.execute(cqlquery)
    return pd.DataFrame(rows)

def getWeatherDF():
    return getDF(WEATHER_TABLE)

def getTwitterDF():
    return getDF(TWITTER_TABLE)

def getSpaceXDF():
    return getDF(SPACEX_TABLE)

def getFakerDF():
    return getDF(FAKER_TABLE)

if __name__ == "__main__":
    action = sys.argv[1]
    target = sys.argv[2]
    targetfile = sys.argv[3]
    if action == "save":
        loadDF(targetfile, target)
    elif action == "get":
        df = getDF(target)
        print(df)
```

Rebuild:

```bash
docker-compose -f data-vis/docker-compose.yml up -d
```

# Data Visualization

![Plot showing data trends](/asset/plot.png)

1. Comparison of Weather Records Between Two Cities

Consistency in Data:
Ho Chi Minh City's recorded temperatures exhibit minimal variation between temp, temp_max, and temp_min. This suggests consistent weather conditions during the data collection period. Hanoi also shows identical values for temp, temp_max, and temp_min throughout the dataset, which might indicate a lack of detailed temperature range measurements or simplified data reporting. Ho Chi Minh City presents values of about 31-32°C, while Hanoi has about 19-20°C, which indicates the climatic difference between the tropical south and the temperate north of the country. 2. Temperature - Humidity - Pressure Relations

2. Humidity vs. Pressure:

Hanoi has a higher value of pressure of about 1018 hPa, whereas Ho Chi Minh City has about 1007 hPa. This is due to the city's position and seasonal weather conditions. Ho Chi Minh City is a bit more humid, with an average of 60-68%, while Hanoi has an average of 50-60%. Although the humidity is lower in Hanoi, its pressure is higher, which could make it more stable. Ho Chi Minh City is thus expected to feel warmer and less comfortable due to its higher humidity.

# Practical Implications of the Project

1. Practical Problem
   Nowadays, the ability to process and analyze enormous volumes of data in different formats in real time poses serious challenges for organizations. Such challenges are critical in sectors such as aerospace, where huge decisions depend on the amalgamation of multiple data streams from weather conditions, sentiment of the public, to technical parameters. For instance, a successful rocket launch depends on several levels of data observation to foresee hazards, evaluate public opinion, and respond to environmental conditions in real time. Understanding this real-time public sentiment on Twitter can be crucial for making strategic decisions in areas related to marketing or disaster management, among others.

2. Solution through Big Data Analysis
   This project addresses these challenges by leveraging Big Data technologies to process, store, and analyze large datasets in real time. Key components include:

- Data Integration and Aggregation: The system will be able to collect real-time data from various sources, including but not limited to SpaceX launch data, Twitter sentiment, weather reports, and simulated scenarios to ensure a holistic view for decision-making.
- Real-Time Insights and Automation: From a practical perspective, the project grants real-time insights, hence enabling rapid, informed organizational decisions with seamless data streaming with Apache Kafka and scalable, distributed storage in Cassandra.
- Scalability and Efficiency: The system was developed to meet the demands for high-volume and high-velocity data in a consistent performance manner that makes the system ideal for very large industrial applications.

3. Impact
   From addressing high volume, velocity, and variety, this Big Data project demonstrates how real-time analytics can be applied to operational efficiency, risk management, and citizen engagement. Be it for aerospace, public safety, or customer relationships, this is the approach that enables organizations and businesses to transform complex data streams into truly usable, actionable insight.
