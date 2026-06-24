from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import HealthProgram, ProgramEnrollment, ProgramOutcome, ProgramMetric
from .serializers import (
    HealthProgramSerializer,
    ProgramEnrollmentSerializer,
    ProgramOutcomeSerializer,
    ProgramMetricSerializer,
)


class NationalProgramsBaseViewSet(viewsets.ModelViewSet):
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


class HealthProgramViewSet(NationalProgramsBaseViewSet):
    queryset = HealthProgram.objects.all()
    serializer_class = HealthProgramSerializer
    filterset_fields = ["program_type", "status", "governing_authority"]
    search_fields = ["program_code", "program_name"]
    ordering_fields = ["program_code", "program_name", "start_date", "created_at"]

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        """Enroll a patient into this program."""
        program = self.get_object()
        patient_id = request.data.get("patient_id")
        enrollment_date = request.data.get("enrollment_date")
        if not patient_id or not enrollment_date:
            return Response(
                {"detail": "patient_id and enrollment_date are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant_id = getattr(request, "tenant_id", None)
        enrollment = ProgramEnrollment.objects.create(
            tenant_id=tenant_id,
            program=program,
            patient_id=patient_id,
            enrollment_date=enrollment_date,
            enrolled_by_user_id=request.data.get("enrolled_by_user_id"),
            enrollment_facility_id=request.data.get("enrollment_facility_id"),
            expected_completion_date=request.data.get("expected_completion_date"),
            notes=request.data.get("notes", ""),
        )
        program.enrolled_count = program.enrollments.filter(
            tenant_id=tenant_id, status="active"
        ).count()
        program.save(update_fields=["enrolled_count", "updated_at"])
        return Response(
            ProgramEnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        """Suspend an active program."""
        program = self.get_object()
        program.status = "suspended"
        program.save(update_fields=["status", "updated_at"])
        return Response({"status": "suspended", "id": str(program.id)})


class ProgramEnrollmentViewSet(NationalProgramsBaseViewSet):
    queryset = ProgramEnrollment.objects.select_related("program")
    serializer_class = ProgramEnrollmentSerializer
    filterset_fields = ["program", "patient_id", "status"]
    search_fields = []
    ordering_fields = ["enrollment_date", "created_at"]

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        """Withdraw an enrolled patient from the program."""
        enrollment = self.get_object()
        enrollment.status = "withdrawn"
        enrollment.save(update_fields=["status", "updated_at"])
        return Response({"status": "withdrawn", "id": str(enrollment.id)})


class ProgramOutcomeViewSet(NationalProgramsBaseViewSet):
    queryset = ProgramOutcome.objects.select_related("program")
    serializer_class = ProgramOutcomeSerializer
    filterset_fields = ["program", "patient_id", "outcome_type"]
    search_fields = ["icd11_code", "loinc_code"]
    ordering_fields = ["outcome_date", "created_at"]


class ProgramMetricViewSet(NationalProgramsBaseViewSet):
    queryset = ProgramMetric.objects.select_related("program")
    serializer_class = ProgramMetricSerializer
    filterset_fields = ["program", "metric_type", "meets_target", "metric_date"]
    search_fields = ["metric_name"]
    ordering_fields = ["metric_date", "metric_name", "created_at"]
