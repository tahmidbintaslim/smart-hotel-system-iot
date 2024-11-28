from kafka import KafkaProducer
import json

class KafkaProducerClient:
    def __init__(self, broker: str):
        self.producer = KafkaProducer(
            bootstrap_servers=broker,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )

    def publish(self, topic: str, message: dict):
        try:
            self.producer.send(topic, message)
            print(f"Published message to topic {topic}: {message}")
        except Exception as e:
            print(f"Failed to publish message to topic {topic}: {e}")
