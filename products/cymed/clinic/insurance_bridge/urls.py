from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.clinic.insurance_bridge.views import (
    PayerViewSet, InsurancePlanViewSet, EligibilityCheckViewSet,
    AuthorizationRequestViewSet, AuthorizationResponseViewSet
)

router = DefaultRouter()
router.register("payers", PayerViewSet)
router.register("plans", InsurancePlanViewSet)
router.register("eligibility", EligibilityCheckViewSet)
router.register("auth-requests", AuthorizationRequestViewSet)
router.register("auth-responses", AuthorizationResponseViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
