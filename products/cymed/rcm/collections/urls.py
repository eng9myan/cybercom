from rest_framework.routers import DefaultRouter
from .views import (
    CollectionCaseViewSet,
    CollectionActionViewSet,
    PaymentPlanViewSet,
    CollectionOutcomeViewSet,
)

router = DefaultRouter()
router.register(r"cases", CollectionCaseViewSet, basename="collection-case")
router.register(r"actions", CollectionActionViewSet, basename="collection-action")
router.register(r"payment-plans", PaymentPlanViewSet, basename="payment-plan")
router.register(r"outcomes", CollectionOutcomeViewSet, basename="collection-outcome")

urlpatterns = router.urls
