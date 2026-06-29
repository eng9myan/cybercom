from django.urls import include, path
from rest_framework.routers import DefaultRouter

from platform.cyai.views import (
    GuardrailPolicyViewSet,
    InferenceLogViewSet,
    ModelConfigViewSet,
    PromptTemplateViewSet,
)

router = DefaultRouter()
router.register("configs", ModelConfigViewSet, basename="ai-config")
router.register("prompts", PromptTemplateViewSet, basename="ai-prompt")
router.register("guardrails", GuardrailPolicyViewSet, basename="ai-guardrail")
router.register("inference-logs", InferenceLogViewSet, basename="ai-inference-log")

urlpatterns = [
    path("", include(router.urls)),
]
