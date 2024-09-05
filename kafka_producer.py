from confluent_kafka import Producer
import json

# Kafka configuration
conf = {
    'bootstrap.servers': 'kafka:9092'  # Update with your Kafka server address
}

# Create Kafka producer instance
producer = Producer(**conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def send_notification(topic: str, message: dict):
    """Send a notification message to the Kafka topic."""
    producer.produce(topic, value=json.dumps(message).encode('utf-8'), callback=delivery_report)
    producer.poll(1)  # Ensure message is sent
    producer.flush()  # Wait until all messages are delivered
