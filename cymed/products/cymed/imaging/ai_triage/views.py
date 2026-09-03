"""DRF viewsets for CyMed Imaging AI triage models and workflow actions."""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import AiModel, InferenceRun, TriageAlert, TriageFinding, TriageQueue
from .serializers import (
    AiModelSerializer,
    InferenceRunSerializer,
    TriageAlertSerializer,
    TriageFindingSerializer,
    TriageQueueSerializer,
)


class AiModelViewSet(viewsets.ModelViewSet):
    queryset = AiModel.objects.all()
    serializer_class = AiModelSerializer

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        data = request.data
        model = services.register_model(
            vendor=data.get("vendor"),
            product_code=data.get("product_code"),
            version=data.get("version"),
            modality=data.get("modality"),
            body_part=data.get("body_part", ""),
            finding_kinds=data.get("finding_kinds") or [],
            regulatory_kind=data.get("regulatory_kind"),
            regulatory_reference=data.get("regulatory_reference", ""),
            endpoint_url=data.get("endpoint_url", ""),
            auth_kind=data.get("auth_kind", "none"),
            auth_secret_ref=data.get("auth_secret_ref", ""),
            tenant_id=data.get("tenant_id"),
        )
        return Response(AiModelSerializer(model).data, status=status.HTTP_201_CREATED)


class TriageQueueViewSet(viewsets.ModelViewSet):
    queryset = TriageQueue.objects.all()
    serializer_class = TriageQueueSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open(self, request):
        data = request.data
        queue = services.open_queue(
            tenant_id=data.get("tenant_id"),
            code=data.get("code"),
            name=data.get("name"),
            modality=data.get("modality"),
            priority_rules=data.get("priority_rules") or {},
        )
        return Response(TriageQueueSerializer(queue).data, status=status.HTTP_201_CREATED)


class InferenceRunViewSet(viewsets.ModelViewSet):
    queryset = InferenceRun.objects.all()
    serializer_class = InferenceRunSerializer

    @action(detail=False, methods=["post"], url_path="request")
    def request_run(self, request):
        data = request.data
        run = services.request_inference(
            tenant_id=data.get("tenant_id"),
            model_id=data.get("model_id"),
            study_instance_uid=data.get("study_instance_uid"),
            ordered_by_profile_id=data.get("ordered_by_profile_id"),
        )
        return Response(InferenceRunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="dispatch")
    def dispatch(self, request, pk=None):
        run = services.dispatch_run(run_id=pk)
        return Response(InferenceRunSerializer(run).data)


class TriageFindingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TriageFinding.objects.all()
    serializer_class = TriageFindingSerializer


class TriageAlertViewSet(viewsets.ModelViewSet):
    queryset = TriageAlert.objects.all()
    serializer_class = TriageAlertSerializer

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        alert = services.acknowledge_alert(
            alert_id=pk,
            radiologist_profile_id=request.data.get("radiologist_profile_id"),
        )
        return Response(TriageAlertSerializer(alert).data)

    @action(detail=True, methods=["post"], url_path="dismiss")
    def dismiss(self, request, pk=None):
        alert = services.dismiss_alert(
            alert_id=pk,
            reason=request.data.get("reason", ""),
        )
        return Response(TriageAlertSerializer(alert).data)

    @action(detail=True, methods=["post"], url_path="escalate")
    def escalate(self, request, pk=None):
        alert = services.escalate_alert(
            alert_id=pk,
            escalate_to_profile_id=request.data.get("escalate_to_profile_id"),
        )
        return Response(TriageAlertSerializer(alert).data)
