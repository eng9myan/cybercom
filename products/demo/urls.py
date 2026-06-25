from rest_framework.routers import DefaultRouter
from .views import (
    DemoEnvironmentViewSet, DemoTenantViewSet, DemoScenarioViewSet,
    DemoSessionViewSet, DemoResetRequestViewSet, ProductTourViewSet,
)

router = DefaultRouter()
router.register("environments", DemoEnvironmentViewSet, basename="demo-environment")
router.register("tenants", DemoTenantViewSet, basename="demo-tenant")
router.register("scenarios", DemoScenarioViewSet, basename="demo-scenario")
router.register("sessions", DemoSessionViewSet, basename="demo-session")
router.register("reset-requests", DemoResetRequestViewSet, basename="demo-reset-request")
router.register("product-tours", ProductTourViewSet, basename="product-tour")

urlpatterns = router.urls
