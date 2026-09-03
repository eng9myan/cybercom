"""ViewSets for CyMed MRFF ai_diagnostics sub-app."""
from __future__ import annotations

from decimal import Decimal

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    BiasAudit,
    Deployment,
    DriftMetric,
    HitlReviewItem,
    HitlReviewQueue,
    InferenceOutcome,
    ModelCard,
)
from .serializers import (
    BiasAuditSerializer,
    DeploymentSerializer,
    DriftMetricSerializer,
    HitlReviewItemSerializer,
    HitlReviewQueueSerializer,
    InferenceOutcomeSerializer,
    ModelCardSerializer,
)


class ModelCardViewSet(viewsets.ModelViewSet):
    queryset = ModelCard.objects.all()
    serializer_class = ModelCardSerializer

    @action(detail=False, methods=["post"], url_path="publish")
    def publish(self, request):
        card = services.publish_model_card(
            ai_model_id=request.data.get("ai_model_id"),
            version=request.data.get("version"),
            intended_use=request.data.get("intended_use", ""),
            tenant_id=request.data.get("tenant_id"),
            target_population=request.data.get("target_population", ""),
            clinical_workflow=request.data.get("clinical_workflow", ""),
            inputs_description=request.data.get("inputs_description", ""),
            outputs_description=request.data.get("outputs_description", ""),
            performance=request.data.get("performance"),
            validation_datasets=request.data.get("validation_datasets"),
            known_limitations=request.data.get("known_limitations", ""),
            ethical_considerations=request.data.get("ethical_considerations", ""),
            maintainer_email=request.data.get("maintainer_email", ""),
            regulatory_kind=request.data.get("regulatory_kind", "unknown"),
            regulatory_reference=request.data.get("regulatory_reference", ""),
            tga_artg_number=request.data.get("tga_artg_number", ""),
        )
        return Response(ModelCardSerializer(card).data)


class DeploymentViewSet(viewsets.ModelViewSet):
    queryset = Deployment.objects.all()
    serializer_class = DeploymentSerializer

    @action(detail=False, methods=["post"], url_path="deploy")
    def deploy(self, request):
        deployment = services.deploy(
            tenant_id=request.data.get("tenant_id"),
            ai_model_id=request.data.get("ai_model_id"),
            version=request.data.get("version"),
            environment=request.data.get("environment", "canary"),
            traffic_percent=int(request.data.get("traffic_percent", 10)),
            deployed_by_profile_id=request.data.get("deployed_by_profile_id"),
        )
        return Response(DeploymentSerializer(deployment).data)

    @action(detail=True, methods=["post"], url_path="promote")
    def promote(self, request, pk=None):
        deployment = services.promote(
            deployment_id=pk,
            environment=request.data.get("environment"),
            traffic_percent=int(request.data.get("traffic_percent", 100)),
        )
        return Response(DeploymentSerializer(deployment).data)

    @action(detail=True, methods=["post"], url_path="retire")
    def retire(self, request, pk=None):
        deployment = services.retire(
            deployment_id=pk,
            rollback_reason=request.data.get("rollback_reason", ""),
        )
        return Response(DeploymentSerializer(deployment).data)

    @action(detail=True, methods=["post"], url_path="record-outcome")
    def record_outcome(self, request, pk=None):
        outcome = services.record_outcome(
            deployment_id=pk,
            study_instance_uid=request.data.get("study_instance_uid"),
            inference_run_id=request.data.get("inference_run_id"),
            predicted_kind=request.data.get("predicted_kind", ""),
            predicted_confidence=Decimal(str(request.data.get("predicted_confidence", "0"))),
            ground_truth_kind=request.data.get("ground_truth_kind", ""),
            ground_truth_source=request.data.get("ground_truth_source", "unknown"),
            reviewer_profile_id=request.data.get("reviewer_profile_id"),
            note=request.data.get("note", ""),
        )
        return Response(InferenceOutcomeSerializer(outcome).data)

    @action(detail=True, methods=["post"], url_path="capture-drift")
    def capture_drift(self, request, pk=None):
        metric = services.capture_drift(
            tenant_id=request.data.get("tenant_id"),
            deployment_id=pk,
            window_start=request.data.get("window_start"),
            window_end=request.data.get("window_end"),
            metric_kind=request.data.get("metric_kind"),
            score=Decimal(str(request.data.get("score", "0"))),
            threshold=Decimal(str(request.data.get("threshold", "0.05"))),
            details=request.data.get("details"),
        )
        return Response(DriftMetricSerializer(metric).data)


class InferenceOutcomeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InferenceOutcome.objects.all()
    serializer_class = InferenceOutcomeSerializer


class DriftMetricViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DriftMetric.objects.all()
    serializer_class = DriftMetricSerializer


class HitlReviewQueueViewSet(viewsets.ModelViewSet):
    queryset = HitlReviewQueue.objects.all()
    serializer_class = HitlReviewQueueSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open_queue(self, request):
        queue = services.open_review_queue(
            tenant_id=request.data.get("tenant_id"),
            code=request.data.get("code"),
            name=request.data.get("name"),
            trigger_rules=request.data.get("trigger_rules"),
            priority=int(request.data.get("priority", 100)),
        )
        return Response(HitlReviewQueueSerializer(queue).data)

    @action(detail=True, methods=["post"], url_path="enqueue")
    def enqueue(self, request, pk=None):
        item = services.enqueue_review(
            queue_id=pk,
            inference_run_id=request.data.get("inference_run_id"),
            study_instance_uid=request.data.get("study_instance_uid"),
            priority=request.data.get("priority", "routine"),
        )
        return Response(HitlReviewItemSerializer(item).data)


class HitlReviewItemViewSet(viewsets.ModelViewSet):
    queryset = HitlReviewItem.objects.all()
    serializer_class = HitlReviewItemSerializer

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        item = services.assign_review(
            item_id=pk,
            reviewer_profile_id=request.data.get("reviewer_profile_id"),
        )
        return Response(HitlReviewItemSerializer(item).data)

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        item = services.resolve_review(
            item_id=pk,
            status=request.data.get("status"),
            override_kind=request.data.get("override_kind", ""),
            override_reason=request.data.get("override_reason", ""),
        )
        return Response(HitlReviewItemSerializer(item).data)


class BiasAuditViewSet(viewsets.ModelViewSet):
    queryset = BiasAudit.objects.all()
    serializer_class = BiasAuditSerializer

    @action(detail=False, methods=["post"], url_path="record")
    def record(self, request):
        audit = services.record_bias_audit(
            tenant_id=request.data.get("tenant_id"),
            ai_model_id=request.data.get("ai_model_id"),
            version=request.data.get("version", ""),
            cohort_kind=request.data.get("cohort_kind"),
            cohort_value=request.data.get("cohort_value", ""),
            sample_size=int(request.data.get("sample_size", 0)),
            auc=request.data.get("auc"),
            sensitivity=request.data.get("sensitivity"),
            specificity=request.data.get("specificity"),
            false_positive_rate=request.data.get("false_positive_rate"),
            false_negative_rate=request.data.get("false_negative_rate"),
            note=request.data.get("note", ""),
        )
        return Response(BiasAuditSerializer(audit).data)
