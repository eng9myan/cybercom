from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.product_catalog.views import (
    ProductFeatureMatrixViewSet,
    ProductLicenseMappingViewSet,
    ProductVersionViewSet,
)

router = DefaultRouter()
router.register("versions", ProductVersionViewSet)
router.register("license-mappings", ProductLicenseMappingViewSet)
router.register("feature-matrix", ProductFeatureMatrixViewSet)

urlpatterns = [path("", include(router.urls))]
