import json
import logging
import os

from confluent_kafka import Producer

logger = logging.getLogger(__name__)

_producer = None


def _get_producer() -> Producer:
    global _producer
    if _producer is None:
        bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        _producer = Producer({"bootstrap.servers": bootstrap_servers})
    return _producer


def publish_event(topic: str, payload: dict) -> None:
    producer = _get_producer()
    try:
        value = json.dumps(payload).encode("utf-8")
        producer.produce(topic, value=value)
        producer.flush()
    except Exception as exc:
        logger.error("Failed to publish event to topic %s — payload: %s — error: %s", topic, payload, exc)
