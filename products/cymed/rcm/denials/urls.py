from rest_framework.routers import DefaultRouter

from .views import (
    AppealOutcomeViewSet,
    AppealViewSet,
    CorrectiveActionViewSet,
    DenialReasonViewSet,
    DenialViewSet,
)

router = DefaultRouter()
router.register(r"denials", DenialViewSet, basename="denial")
router.register(r"denial-reasons", DenialReasonViewSet, basename="denial-reason")
router.register(r"appeals", AppealViewSet, basename="appeal")
router.register(r"appeal-outcomes", AppealOutcomeViewSet, basename="appeal-outcome")
router.register(r"corrective-actions", CorrectiveActionViewSet, basename="corrective-action")

urlpatterns = router.urls
