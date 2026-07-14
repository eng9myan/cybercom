from django.utils import timezone

from platform.events.models import OutboxEvent, OutboxEventStatus
from platform.events.publisher import KafkaEventPublisher


class EventReplayManager:
    """
    Manages historical event replay and DLQ re-publishing for downstream consumers.
    """

    @classmethod
    def replay_events(
        cls,
        tenant_id: str,
        topic: str,
        start_time: timezone.datetime | None = None,
        end_time: timezone.datetime | None = None,
        event_types: list[str] | None = None,
    ) -> int:
        queryset = OutboxEvent.objects.filter(tenant_id=tenant_id, topic=topic)
        if start_time:
            queryset = queryset.filter(created_at__gte=start_time)
        if end_time:
            queryset = queryset.filter(created_at__lte=end_time)
        if event_types:
            queryset = queryset.filter(event_type__in=event_types)

        replayed_count = 0
        for event in queryset:
            # Re-publish using KafkaEventPublisher
            success = KafkaEventPublisher.publish(
                topic=event.topic,
                key=str(event.id),
                payload=event.payload,
                headers={
                    **event.headers,
                    "x-replay": "true",
                    "x-original-created-at": event.created_at.isoformat(),
                },
            )
            if success:
                replayed_count += 1

        return replayed_count

    @classmethod
    def replay_failed_events(cls, tenant_id: str, topic: str | None = None) -> int:
        queryset = OutboxEvent.objects.filter(tenant_id=tenant_id, status=OutboxEventStatus.FAILED)
        if topic:
            queryset = queryset.filter(topic=topic)

        replayed_count = 0
        for event in queryset:
            success = KafkaEventPublisher.publish(
                topic=event.topic, key=str(event.id), payload=event.payload, headers=event.headers
            )
            if success:
                event.mark_published()
                replayed_count += 1

        return replayed_count
