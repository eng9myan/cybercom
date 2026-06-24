rom django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    SurveillanceCase,
    Outbreak,
    OutbreakAlert,
    PublicHealthEvent,
    CaseInvestigation,
)
from .serializers import (
    SurveillanceCaseSerializer,
    OutbreakSerializer,
    OutbreakAlertSerializer,
    PublicHealthEventSerializer,
    CaseInvestigationSerializer,
)


class PopulationHealthModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class SurveillanceCaseViewSet(PopulationHealthModelViewSet):
    queryset = SurveillanceCase.objects.all()
    serializer_class = SurveillanceCaseSerializer
    filterset_fields = ["disease_code", "case_type", "status", "is_notifiable"]
    search_fields = ["disease_code", "disease_name"]
    ordering_fields = ["case_date", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        case_date = self.request.query_params.get("case_date")
        if case_date:
            qs = qs.filter(case_date=case_date)
        return qs

    @action(detail=True, methods=["post"])
    def notify_authority(self, request, pk=None):
        case = self.get_object()
        case.notification_sent = True
        case.notification_sent_at = timezone.now()
        case.save(update_fields=["notification_sent", "notification_sent_at", "updated_at"])
        return Response({
            "status": "notification_sent",
            "id": str(case.id),
            "notification_sent_at": case.notification_sent_at.isoformat(),
        })


class OutbreakViewSet(PopulationHealthModelViewSet):
    queryset = Outbreak.objects.all()
    serializer_class = OutbreakSerializer
    filterset_fields = ["disease_code", "status", "severity_level"]
    search_fields = ["disease_code", "disease_name", "geographic_scope"]
    ordering_fields = ["start_date", "affected_count", "created_at"]

    @action(detail=True, methods=["post"])
    def contain(self, request, pk=None):
        outbreak = self.get_object()
        outbreak.status = "contained"
        outbreak.save(update_fields=["status", "updated_at"])
        return Response({"status": "contained", "id": str(outbreak.id)})

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        outbreak = self.get_object()
        outbreak.status = "resolved"
        outbreak.end_date = timezone.now().date()
        outbreak.save(update_fields=["status", "end_date", "updated_at"])
        return Response({"status": "resolved", "id": str(outbreak.id)})


class OutbreakAlertViewSet(PopulationHealthModelViewSet):
    queryset = OutbreakAlert.objects.select_related("outbreak")
    serializer_class = OutbreakAlertSerializer
    filterset_fields = ["outbreak", "alert_level", "is_active"]
    search_fields = ["description", "issued_by_authority"]
    ordering_fields = ["alert_date", "created_at"]


class PublicHealthEventViewSet(PopulationHealthModelViewSet):
    queryset = PublicHealthEvent.objects.all()
    serializer_class = PublicHealthEventSerializer
    filterset_fields = ["event_type", "severity", "response_status"]
    search_fields = ["event_name", "geographic_scope", "responsible_authority"]
    ordering_fields = ["event_date", "created_at"]


class CaseInvestigationViewSet(PopulationHealthModelViewSet):
    queryset = CaseInvestigation.objects.select_related("surveillance_case")
    serializer_class = CaseInvestigationSerializer
    filterset_fields = ["surveillance_case", "outcome"]
    search_fields = ["probable_source", "findings"]
    ordering_fields = ["investigation_date", "created_at"]
