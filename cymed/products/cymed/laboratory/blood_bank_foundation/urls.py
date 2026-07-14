from rest_framework.routers import DefaultRouter

from .views import (
    BloodCompatibilityViewSet,
    BloodInventoryViewSet,
    BloodProductViewSet,
    TransfusionRequestViewSet,
)

router = DefaultRouter()
router.register("products", BloodProductViewSet, basename="lab-blood-products")
router.register("inventory", BloodInventoryViewSet, basename="lab-blood-inventory")
router.register("compatibility", BloodCompatibilityViewSet, basename="lab-blood-compatibility")
router.register(
    "transfusion-requests", TransfusionRequestViewSet, basename="lab-transfusion-requests"
)

urlpatterns = router.urls
