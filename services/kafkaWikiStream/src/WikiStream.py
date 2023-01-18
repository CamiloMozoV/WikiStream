import json
from sys import api_version
from kafka import KafkaProducer
from sseclient import SSEClient as EventSource

kafka_producer = KafkaProducer(
    bootstrap_servers=["spark-kafka:9092"],
    api_version=(2,0,2),
    value_serializer=lambda x: json.dumps(x).encode("utf-8")
)

# Read streaming event
url = "https://stream.wikimedia.org/v2/stream/recentchange"

for event in EventSource(url=url):
    if event.event == "message":
        try:
            change = json.loads(event.data)
        except ValueError:
            pass
        else:
            # Send message to topic "wikistream"
            kafka_producer.send("wikistream", change)