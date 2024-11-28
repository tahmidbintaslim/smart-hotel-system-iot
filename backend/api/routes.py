from fastapi import APIRouter

router = APIRouter()

@router.post("/kafka/publish/")
def kafka_publish(topic: str, message: dict):
    from kafka.producer import KafkaProducerClient
    producer = KafkaProducerClient(broker="kafka:9092")
    producer.publish(topic, message)
    return {"status": "published", "topic": topic, "message": message}

@router.post("/cloud/push/")
def push_to_cloud(data: dict):
    from cloud.azure_integration import push_to_cloud
    push_to_cloud(data)
    return {"status": "pushed to cloud", "data": data}
