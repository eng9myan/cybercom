"""
CyMed Population Health — Reporting Views
"""
import django.utils.timezone as timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import NationalReport, ReportTemplate, GovernmentSubmission, ReportSchedule
from .serializers import (
    NationalReportSerializer,
    ReportTemplateSerializer,
    GovernmentSubmissionSerializer,
    ReportScheduleSerializer,
)


class PopulationHealthModelViewSet(viewsets.ModelViewSet):
    """Base ViewSet that scopes all queries to the current tenant."""

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


class NationalReportViewSet(PopulationHealthModelViewSet):
    """Full CRUD for national health reports with approve and submit actions."""

    queryset = NationalReport.objects.all()
    serializer_class = NationalReportSerializer
    filterset_fields = ["report_type", "status", "report_date"]
    ordering_fields = ["report_name", "report_date", "status", "created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        report = self.get_object()
        if report.status not in ("draft", "in_review"):
            return Response(
                {"detail": "Report must be in draft or in_review status to approve."},
                status=400,
            )
        user_id = getattr(request.user, "id", None)
        report.status = "approved"
        report.approved_by_user_id = user_id
        report.approved_at = timezone.now()
        report.save(update_fields=["status", "approved_by_user_id", "approved_at", "updated_at"])
        serializer = self.get_serializer(report)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        report = self.get_object()
        if report.status != "approved":
            return Response(
                {"detail": "Only approved reports can be submitted."},
                status=400,
            )
        report.status = "submitted"
        report.save(update_fields=["status", "updated_at"])
        serializer = self.get_serializer(report)
        return Response(serializer.data)


class ReportTemplateViewSet(PopulationHealthModelViewSet):
    """Full CRUD for report templates."""

    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    filterset_fields = ["report_type", "is_national_standard", "is_active"]
    search_fields = ["template_name"]
    ordering_fields = ["template_name", "report_type", "version", "created_at"]


class GovernmentSubmissionViewSet(PopulationHealthModelViewSet):
    """Full CRUD for government submissions."""

    queryset = GovernmentSubmission.objects.select_related("national_report")
    serializer_class = GovernmentSubmissionSerializer
    filterset_fields = ["national_report", "status", "submission_method"]
    ordering_fields = ["submission_date", "status", "created_at"]


class ReportScheduleViewSet(PopulationHealthModelViewSet):
    """Full CRUD for report schedules."""

    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    filterset_fields = ["report_type", "frequency", "is_active"]
    ordering_fields = ["schedule_name", "next_due_date", "frequency", "created_at"]
