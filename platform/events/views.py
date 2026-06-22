from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from platform.events.models import OutboxEvent, DeadLetterEvent, EventDeliveryLog
from platform.events.serializers import (
    OutboxEventSerializer,
    DeadLetterEventSerializer,
    EventDeliveryLogSerializer,
    EventReplaySerializer
)
from platform.events.replay import EventReplayManager
from platform.events.signing import EventSigner
import json


class OutboxEventViewSet(viewsets.ModelViewSet):
    queryset = OutboxEvent.objects.all().order_by("-created_at")
    serializer_class = OutboxEventSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="replay")
    def replay(self, request):
        serializer = EventReplaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        count = EventReplayManager.replay_events(
            tenant_id=str(serializer.validated_data["tenant_id"]),
            topic=serializer.validated_data["topic"],
            start_time=serializer.validated_data.get("start_time"),
            end_time=serializer.validated_data.get("end_time"),
            event_types=serializer.validated_data.get("event_types"),
        )
        return Response({"replayed_count": count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="sign")
    def sign_event(self, request, pk=None):
        event = self.get_object()
        payload_str = json.dumps(event.payload, sort_keys=True)
        signature = EventSigner.sign_payload(str(event.tenant_id), payload_str.encode())
        return Response({
            "event_id": event.id,
            "signature": signature
        }, status=status.HTTP_200_OK)


class DeadLetterEventViewSet(viewsets.ModelViewSet):
    queryset = DeadLetterEvent.objects.all().order_by("-failed_at")
    serializer_class = DeadLetterEventSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="retry")
    def retry_failed(self, request):
        tenant_id = request.data.get("tenant_id")
        topic = request.data.get("topic")
        if not tenant_id:
            return Response({"detail": "tenant_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        count = EventReplayManager.replay_failed_events(tenant_id, topic)
        return Response({"retried_count": count}, status=status.HTTP_200_OK)


class EventDeliveryLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EventDeliveryLog.objects.all().order_by("-delivered_at")
    serializer_class = EventDeliveryLogSerializer
    permission_classes = [IsAuthenticated]
