from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.branding.views import (
    BrandAssetViewSet,
    BrandDomainViewSet,
    BrandLocalizationViewSet,
    BrandThemeViewSet,
    BrandViewSet,
)

router = DefaultRouter()
router.register("brands", BrandViewSet)
router.register("themes", BrandThemeViewSet)
router.register("assets", BrandAssetViewSet)
router.register("domains", BrandDomainViewSet)
router.register("localizations", BrandLocalizationViewSet)

urlpatterns = [path("", include(router.urls))]
