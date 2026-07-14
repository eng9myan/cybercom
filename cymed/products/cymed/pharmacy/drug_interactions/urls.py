"""Drug Interactions URL routing."""

from rest_framework.routers import DefaultRouter

from .views import (
    DrugInteractionViewSet,
    InteractionAlertViewSet,
    InteractionRuleViewSet,
    InteractionSeverityViewSet,
)

router = DefaultRouter()
router.register(r"rules", InteractionRuleViewSet, basename="interaction-rule")
router.register(r"detected", DrugInteractionViewSet, basename="drug-interaction")
router.register(r"severity", InteractionSeverityViewSet, basename="interaction-severity")
router.register(r"alerts", InteractionAlertViewSet, basename="interaction-alert")

urlpatterns = router.urls
