"""
Kafka event publisher for CyberCom platform. ADR-0004.
Uses confluent-kafka producer with Avro serialization.
"""

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger("cybercom.events")


class KafkaEventPublisher:
    """
    Publishes domain events to Kafka topics.
    Wraps confluent-kafka Producer with platform conventions.
    """

    _producer = None

    @classmethod
    def get_producer(cls):
        if cls._producer is None:
            try:
                from confluent_kafka import Producer

                cls._producer = Producer(
                    {
                        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                        "security.protocol": settings.KAFKA_SECURITY_PROTOCOL,
                        "acks": "all",
                        "enable.idempotence": True,
                        "compression.type": "snappy",
                    }
                )
            except ImportError:
                logger.warning("confluent-kafka not available; event publishing disabled.")
        return cls._producer

    @classmethod
    def publish(
        cls, topic: str, key: str, payload: dict[str, Any], headers: dict | None = None
    ) -> bool:
        producer = cls.get_producer()
        if producer is None:
            return False

        try:
            producer.produce(
                topic=topic,
                key=key.encode("utf-8"),
                value=json.dumps(payload).encode("utf-8"),
                headers=[(k, v.encode()) for k, v in (headers or {}).items()],
                on_delivery=cls._delivery_callback,
            )
            producer.poll(0)
            return True
        except Exception as exc:
            logger.error("Kafka publish failed", extra={"topic": topic, "error": str(exc)})
            return False

    @staticmethod
    def _delivery_callback(err, msg) -> None:
        if err:
            logger.error("Kafka delivery failed", extra={"error": str(err)})
        else:
            logger.debug("Kafka delivery ok", extra={"topic": msg.topic(), "offset": msg.offset()})
