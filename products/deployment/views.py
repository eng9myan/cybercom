from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    DeploymentRecord, EnvironmentCheck, DeploymentStep,
    TenantProvision, BackupRecord, HealthCheckSnapshot, UpgradeRecord,
)
from .serializers import (
    DeploymentRecordSerializer, EnvironmentCheckSerializer, DeploymentStepSerializer,
    TenantProvisionSerializer, BackupRecordSerializer, HealthCheckSnapshotSerializer,
    UpgradeRecordSerializer,
)


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request, "tenant_id", None))


class DeploymentRecordViewSet(BaseViewSet):
    queryset = DeploymentRecord.objects.all()
    serializer_class = DeploymentRecordSerializer
    filterset_fields = ["deployment_type", "tenancy_model", "infrastructure", "status", "country_code"]
    search_fields = ["customer_name", "deployment_code", "region"]
    ordering_fields = ["customer_name", "status", "go_live_date", "created_at"]

    @action(detail=True, methods=["post"])
    def advance_status(self, request, pk=None):
        record = self.get_object()
        transitions = {
            "planned": "validating",
            "validating": "provisioning",
            "provisioning": "installing",
            "installing": "configuring",
            "configuring": "testing",
            "testing": "go_live",
            "go_live": "live",
        }
        next_status = transitions.get(record.status)
        if next_status:
            record.status = next_status
            record.save(update_fields=["status", "updated_at"])
        return Response({"status": record.status, "id": str(record.id)})

    @action(detail=True, methods=["get"])
    def steps(self, request, pk=None):
        record = self.get_object()
        qs = record.steps.all()
        return Response(DeploymentStepSerializer(qs, many=True).data)

    @action(detail=True, methods=["get"])
    def health(self, request, pk=None):
        record = self.get_object()
        snapshot = record.health_snapshots.order_by("-checked_at").first()
        if snapshot:
            return Response(HealthCheckSnapshotSerializer(snapshot).data)
        return Response({"overall_status": "unknown"})


class EnvironmentCheckViewSet(BaseViewSet):
    queryset = EnvironmentCheck.objects.select_related("deployment")
    serializer_class = EnvironmentCheckSerializer
    filterset_fields = ["deployment", "check_category", "passed"]
    ordering_fields = ["checked_at", "created_at"]
    http_method_names = ["get", "post", "head", "options"]


class DeploymentStepViewSet(BaseViewSet):
    queryset = DeploymentStep.objects.select_related("deployment")
    serializer_class = DeploymentStepSerializer
    filterset_fields = ["deployment", "status", "step_category"]
    ordering_fields = ["step_order", "started_at", "created_at"]

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        step = self.get_object()
        step.status = "in_progress"
        step.started_at = timezone.now()
        step.save(update_fields=["status", "started_at", "updated_at"])
        return Response({"status": "in_progress"})

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        step = self.get_object()
        step.status = "completed"
        step.completed_at = timezone.now()
        step.output_log = request.data.get("output_log", "")
        step.save(update_fields=["status", "completed_at", "output_log", "updated_at"])
        return Response({"status": "completed"})

    @action(detail=True, methods=["post"])
    def fail(self, request, pk=None):
        step = self.get_object()
        step.status = "failed"
        step.error_detail = request.data.get("error_detail", "")
        step.save(update_fields=["status", "error_detail", "updated_at"])
        return Response({"status": "failed"})


class TenantProvisionViewSet(BaseViewSet):
    queryset = TenantProvision.objects.select_related("deployment")
    serializer_class = TenantProvisionSerializer
    filterset_fields = ["deployment", "status", "edition", "country_config"]
    search_fields = ["tenant_name", "tenant_slug", "admin_email"]
    ordering_fields = ["tenant_name", "provisioned_at", "created_at"]


class BackupRecordViewSet(BaseViewSet):
    queryset = BackupRecord.objects.select_related("deployment")
    serializer_class = BackupRecordSerializer
    filterset_fields = ["deployment", "backup_type", "status"]
    ordering_fields = ["started_at", "completed_at", "created_at"]


class HealthCheckSnapshotViewSet(BaseViewSet):
    queryset = HealthCheckSnapshot.objects.select_related("deployment")
    serializer_class = HealthCheckSnapshotSerializer
    filterset_fields = ["deployment", "overall_status"]
    ordering_fields = ["checked_at", "created_at"]
    http_method_names = ["get", "post", "head", "options"]


class UpgradeRecordViewSet(BaseViewSet):
    queryset = UpgradeRecord.objects.select_related("deployment")
    serializer_class = UpgradeRecordSerializer
    filterset_fields = ["deployment", "upgrade_type", "status"]
    ordering_fields = ["scheduled_at", "started_at", "created_at"]
