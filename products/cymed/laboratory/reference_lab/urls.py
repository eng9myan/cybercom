from rest_framework.routers import DefaultRouter
from .views import ReferenceLabViewSet, ReferenceLabRoutingViewSet, ReferenceLabOrderViewSet, ReferenceLabResultViewSet

router = DefaultRouter()
router.register("reference-labs", ReferenceLabViewSet, basename="lab-reference-labs")
router.register("routing", ReferenceLabRoutingViewSet, basename="lab-reference-routing")
router.register("reference-orders", ReferenceLabOrderViewSet, basename="lab-reference-orders")
router.register("reference-results", ReferenceLabResultViewSet, basename="lab-reference-results")

urlpatterns = router.urls
