from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from platform.events.models import OutboxEvent
from products.cymed.core.encounters.models import Encounter, EpisodeOfCare
from products.cymed.core.encounters.serializers import EncounterSerializer, EpisodeOfCareSerializer


class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all()
    serializer_class = EncounterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Starts a planned encounter."""
        enc = self.get_object()
        enc.status = "in_progress"
        enc.start_time = timezone.now()
        enc.save()

        # Publish outbox event
        OutboxEvent.objects.create(
            tenant_id=enc.tenant_id,
            topic="cymed.encounter.events",
            event_type="cymed.encounter.started",
            payload={"encounter_id": str(enc.id), "started_at": enc.start_time.isoformat()},
        )

        return Response({"status": enc.status, "start_time": enc.start_time})

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """Closes an arrived or in-progress encounter."""
        enc = self.get_object()
        enc.status = "finished"
        enc.end_time = timezone.now()
        enc.save()

        # Publish outbox event
        OutboxEvent.objects.create(
            tenant_id=enc.tenant_id,
            topic="cymed.encounter.events",
            event_type="cymed.encounter.closed",
            payload={"encounter_id": str(enc.id), "closed_at": enc.end_time.isoformat()},
        )

        return Response({"status": enc.status, "end_time": enc.end_time})


class EpisodeOfCareViewSet(viewsets.ModelViewSet):
    queryset = EpisodeOfCare.objects.all()
    serializer_class = EpisodeOfCareSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
