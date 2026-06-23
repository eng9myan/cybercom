from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.product_catalog.views import (
    ProductVersionViewSet, ProductLicenseMappingViewSet, ProductFeatureMatrixViewSet
)

router = DefaultRouter()
router.register("versions", ProductVersionViewSet)
router.register("license-mappings", ProductLicenseMappingViewSet)
router.register("feature-matrix", ProductFeatureMatrixViewSet)

urlpatterns = [path("", include(router.urls))]
