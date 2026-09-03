"""URL routes for CyMed MRFF ai_diagnostics sub-app."""
from __future__ import annotations

from django.urls import path

from .views import (
    BiasAuditViewSet,
    DeploymentViewSet,
    DriftMetricViewSet,
    HitlReviewItemViewSet,
    HitlReviewQueueViewSet,
    InferenceOutcomeViewSet,
    ModelCardViewSet,
)


urlpatterns = [
    path(
        "model-cards/",
        ModelCardViewSet.as_view({"get": "list", "post": "create"}),
        name="ai-diagnostics-modelcard-list",
    ),
    path(
        "model-cards/<uuid:pk>/",
        ModelCardViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="ai-diagnostics-modelcard-detail",
    ),
    path(
        "model-cards/publish/",
        ModelCardViewSet.as_view({"post": "publish"}),
        name="ai-diagnostics-modelcard-publish",
    ),
    path(
        "deployments/",
        DeploymentViewSet.as_view({"get": "list", "post": "create"}),
        name="ai-diagnostics-deployment-list",
    ),
    path(
        "deployments/<uuid:pk>/",
        DeploymentViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="ai-diagnostics-deployment-detail",
    ),
    path(
        "deployments/deploy/",
        DeploymentViewSet.as_view({"post": "deploy"}),
        name="ai-diagnostics-deployment-deploy",
    ),
    path(
        "deployments/<uuid:pk>/promote/",
        DeploymentViewSet.as_view({"post": "promote"}),
        name="ai-diagnostics-deployment-promote",
    ),
    path(
        "deployments/<uuid:pk>/retire/",
        DeploymentViewSet.as_view({"post": "retire"}),
        name="ai-diagnostics-deployment-retire",
    ),
    path(
        "deployments/<uuid:pk>/record-outcome/",
        DeploymentViewSet.as_view({"post": "record_outcome"}),
        name="ai-diagnostics-deployment-record-outcome",
    ),
    path(
        "deployments/<uuid:pk>/capture-drift/",
        DeploymentViewSet.as_view({"post": "capture_drift"}),
        name="ai-diagnostics-deployment-capture-drift",
    ),
    path(
        "inference-outcomes/",
        InferenceOutcomeViewSet.as_view({"get": "list"}),
        name="ai-diagnostics-inferenceoutcome-list",
    ),
    path(
        "inference-outcomes/<uuid:pk>/",
        InferenceOutcomeViewSet.as_view({"get": "retrieve"}),
        name="ai-diagnostics-inferenceoutcome-detail",
    ),
    path(
        "drift-metrics/",
        DriftMetricViewSet.as_view({"get": "list"}),
        name="ai-diagnostics-driftmetric-list",
    ),
    path(
        "drift-metrics/<uuid:pk>/",
        DriftMetricViewSet.as_view({"get": "retrieve"}),
        name="ai-diagnostics-driftmetric-detail",
    ),
    path(
        "hitl-queues/",
        HitlReviewQueueViewSet.as_view({"get": "list", "post": "create"}),
        name="ai-diagnostics-hitlqueue-list",
    ),
    path(
        "hitl-queues/<uuid:pk>/",
        HitlReviewQueueViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="ai-diagnostics-hitlqueue-detail",
    ),
    path(
        "hitl-queues/open/",
        HitlReviewQueueViewSet.as_view({"post": "open_queue"}),
        name="ai-diagnostics-hitlqueue-open",
    ),
    path(
        "hitl-queues/<uuid:pk>/enqueue/",
        HitlReviewQueueViewSet.as_view({"post": "enqueue"}),
        name="ai-diagnostics-hitlqueue-enqueue",
    ),
    path(
        "hitl-items/",
        HitlReviewItemViewSet.as_view({"get": "list", "post": "create"}),
        name="ai-diagnostics-hitlitem-list",
    ),
    path(
        "hitl-items/<uuid:pk>/",
        HitlReviewItemViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="ai-diagnostics-hitlitem-detail",
    ),
    path(
        "hitl-items/<uuid:pk>/assign/",
        HitlReviewItemViewSet.as_view({"post": "assign"}),
        name="ai-diagnostics-hitlitem-assign",
    ),
    path(
        "hitl-items/<uuid:pk>/resolve/",
        HitlReviewItemViewSet.as_view({"post": "resolve"}),
        name="ai-diagnostics-hitlitem-resolve",
    ),
    path(
        "bias-audits/",
        BiasAuditViewSet.as_view({"get": "list", "post": "create"}),
        name="ai-diagnostics-biasaudit-list",
    ),
    path(
        "bias-audits/<uuid:pk>/",
        BiasAuditViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="ai-diagnostics-biasaudit-detail",
    ),
    path(
        "bias-audits/record/",
        BiasAuditViewSet.as_view({"post": "record"}),
        name="ai-diagnostics-biasaudit-record",
    ),
]
