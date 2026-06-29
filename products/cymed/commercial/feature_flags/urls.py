from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.feature_flags.views import (
    CustomerFeatureViewSet,
    FeatureDependencyViewSet,
    FeatureFlagViewSet,
    TenantFeatureViewSet,
)

router = DefaultRouter()
router.register("flags", FeatureFlagViewSet)
router.register("dependencies", FeatureDependencyViewSet)
router.register("tenant-features", TenantFeatureViewSet)
router.register("customer-features", CustomerFeatureViewSet)

urlpatterns = [path("", include(router.urls))]
