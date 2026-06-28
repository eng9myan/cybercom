from rest_framework.routers import DefaultRouter
from .views import (
    SurveillanceCaseViewSet,
    OutbreakViewSet,
    OutbreakAlertViewSet,
    PublicHealthEventViewSet,
    CaseInvestigationViewSet,
)

router = DefaultRouter()
router.register("cases", SurveillanceCaseViewSet, basename="surveillance-case")
router.register("outbreaks", OutbreakViewSet, basename="outbreak")
router.register("outbreak-alerts", OutbreakAlertViewSet, basename="outbreak-alert")
router.register("public-health-events", PublicHealthEventViewSet, basename="public-health-event")
router.register("case-investigations", CaseInvestigationViewSet, basename="case-investigation")

urlpatterns = router.urls
