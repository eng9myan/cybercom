from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.editions.views import (
    EditionFeatureViewSet,
    EditionLimitViewSet,
    EditionModuleViewSet,
    ProductCatalogEntryViewSet,
    ProductEditionViewSet,
)

router = DefaultRouter()
router.register("products", ProductCatalogEntryViewSet)
router.register("editions", ProductEditionViewSet)
router.register("edition-features", EditionFeatureViewSet)
router.register("edition-limits", EditionLimitViewSet)
router.register("edition-modules", EditionModuleViewSet)

urlpatterns = [path("", include(router.urls))]
