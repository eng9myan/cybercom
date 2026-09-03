"""Explicit URL patterns for CyMed Imaging AI triage viewsets."""

from django.urls import path

from .views import (
    AiModelViewSet,
    InferenceRunViewSet,
    TriageAlertViewSet,
    TriageFindingViewSet,
    TriageQueueViewSet,
)


ai_model_list = AiModelViewSet.as_view({"get": "list", "post": "create"})
ai_model_detail = AiModelViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
ai_model_register = AiModelViewSet.as_view({"post": "register"})

triage_queue_list = TriageQueueViewSet.as_view({"get": "list", "post": "create"})
triage_queue_detail = TriageQueueViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
triage_queue_open = TriageQueueViewSet.as_view({"post": "open"})

inference_run_list = InferenceRunViewSet.as_view({"get": "list", "post": "create"})
inference_run_detail = InferenceRunViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
inference_run_request = InferenceRunViewSet.as_view({"post": "request_run"})
inference_run_dispatch = InferenceRunViewSet.as_view({"post": "dispatch"})

triage_finding_list = TriageFindingViewSet.as_view({"get": "list"})
triage_finding_detail = TriageFindingViewSet.as_view({"get": "retrieve"})

triage_alert_list = TriageAlertViewSet.as_view({"get": "list", "post": "create"})
triage_alert_detail = TriageAlertViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
triage_alert_acknowledge = TriageAlertViewSet.as_view({"post": "acknowledge"})
triage_alert_dismiss = TriageAlertViewSet.as_view({"post": "dismiss"})
triage_alert_escalate = TriageAlertViewSet.as_view({"post": "escalate"})


urlpatterns = [
    path("ai-models/", ai_model_list, name="cymed-img-ai-model-list"),
    path("ai-models/register/", ai_model_register, name="cymed-img-ai-model-register"),
    path("ai-models/<uuid:pk>/", ai_model_detail, name="cymed-img-ai-model-detail"),

    path("triage-queues/", triage_queue_list, name="cymed-img-triage-queue-list"),
    path("triage-queues/open/", triage_queue_open, name="cymed-img-triage-queue-open"),
    path("triage-queues/<uuid:pk>/", triage_queue_detail, name="cymed-img-triage-queue-detail"),

    path("inference-runs/", inference_run_list, name="cymed-img-inference-run-list"),
    path("inference-runs/request/", inference_run_request, name="cymed-img-inference-run-request"),
    path("inference-runs/<uuid:pk>/", inference_run_detail, name="cymed-img-inference-run-detail"),
    path("inference-runs/<uuid:pk>/dispatch/", inference_run_dispatch, name="cymed-img-inference-run-dispatch"),

    path("triage-findings/", triage_finding_list, name="cymed-img-triage-finding-list"),
    path("triage-findings/<uuid:pk>/", triage_finding_detail, name="cymed-img-triage-finding-detail"),

    path("triage-alerts/", triage_alert_list, name="cymed-img-triage-alert-list"),
    path("triage-alerts/<uuid:pk>/", triage_alert_detail, name="cymed-img-triage-alert-detail"),
    path("triage-alerts/<uuid:pk>/acknowledge/", triage_alert_acknowledge, name="cymed-img-triage-alert-acknowledge"),
    path("triage-alerts/<uuid:pk>/dismiss/", triage_alert_dismiss, name="cymed-img-triage-alert-dismiss"),
    path("triage-alerts/<uuid:pk>/escalate/", triage_alert_escalate, name="cymed-img-triage-alert-escalate"),
]
