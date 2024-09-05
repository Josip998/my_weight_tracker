from confluent_kafka import Consumer
from sqlalchemy.orm import Session
from models import Notification
from database import SessionLocal
import json

# Kafka configuration
conf = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'notification-consumer-group',
    'auto.offset.reset': 'earliest'
}

# Create Kafka consumer instance
consumer = Consumer(conf)
consumer.subscribe(['weight-notifications'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def consume_notifications():
    db = next(get_db())
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Error: {msg.error()}")
            continue

        # Parse the message
        notification = json.loads(msg.value().decode('utf-8'))
        user_id = notification['user_id']
        message = notification['message']

        # Create a new Notification instance
        db_notification = Notification(user_id=user_id, message=message)
        db.add(db_notification)
        db.commit()

    consumer.close()

if __name__ == "__main__":
    consume_notifications()
