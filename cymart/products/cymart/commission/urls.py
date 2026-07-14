from rest_framework.routers import DefaultRouter

from .views import CommissionCalculationViewSet, CommissionPolicyViewSet

router = DefaultRouter()
router.register("policies", CommissionPolicyViewSet, basename="commission-policy")
router.register("calculations", CommissionCalculationViewSet, basename="commission-calculation")

urlpatterns = router.urls
