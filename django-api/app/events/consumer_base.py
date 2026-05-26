import logging
import os
import time

from confluent_kafka import Consumer, Producer

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BACKOFF_SECONDS = [1, 2, 4]

_dlq_producer = None


def _get_dlq_producer() -> Producer:
    global _dlq_producer
    if _dlq_producer is None:
        bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        _dlq_producer = Producer({"bootstrap.servers": bootstrap_servers})
    return _dlq_producer


def make_consumer(group_id: str, topics: list[str]) -> Consumer:
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    consumer = Consumer({
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe(topics)
    return consumer


def handle_with_retry(handler, msg, topic: str) -> None:
    last_exc = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            handler(msg)
            return
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                sleep_secs = _BACKOFF_SECONDS[attempt]
                logger.warning(
                    "Handler failed (attempt %d/%d) for topic %s: %s — retrying in %ds",
                    attempt + 1, _MAX_RETRIES, topic, exc, sleep_secs,
                )
                time.sleep(sleep_secs)

    logger.error("Handler exhausted retries for topic %s: %s — sending to DLQ", topic, last_exc)
    dlq_producer = _get_dlq_producer()
    raw = msg.value() if callable(msg.value) else msg.value
    dlq_producer.produce(f"{topic}.dlq", value=raw)
    dlq_producer.flush()


def consume_loop(group_id: str, topics: list[str], handler) -> None:
    consumer = make_consumer(group_id, topics)
    logger.info("Consumer %s started, subscribed to %s", group_id, topics)
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error: %s", msg.error())
                continue
            handle_with_retry(handler, msg, msg.topic())
            consumer.commit(msg)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
