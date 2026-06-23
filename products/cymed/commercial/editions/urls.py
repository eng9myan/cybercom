from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.editions.views import (
    ProductCatalogEntryViewSet, ProductEditionViewSet,
    EditionFeatureViewSet, EditionLimitViewSet, EditionModuleViewSet
)

router = DefaultRouter()
router.register("products", ProductCatalogEntryViewSet)
router.register("editions", ProductEditionViewSet)
router.register("edition-features", EditionFeatureViewSet)
router.register("edition-limits", EditionLimitViewSet)
router.register("edition-modules", EditionModuleViewSet)

urlpatterns = [path("", include(router.urls))]
