from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.feature_flags.views import (
    FeatureFlagViewSet, FeatureDependencyViewSet,
    TenantFeatureViewSet, CustomerFeatureViewSet
)

router = DefaultRouter()
router.register("flags", FeatureFlagViewSet)
router.register("dependencies", FeatureDependencyViewSet)
router.register("tenant-features", TenantFeatureViewSet)
router.register("customer-features", CustomerFeatureViewSet)

urlpatterns = [path("", include(router.urls))]
