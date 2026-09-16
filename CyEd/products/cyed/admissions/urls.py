from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.admissions.views import (
    ApplicationDocumentViewSet,
    ApplicationViewSet,
    CatchmentZoneViewSet,
    OfferViewSet,
)

router = DefaultRouter()
router.register("applications", ApplicationViewSet)
router.register("offers", OfferViewSet)
router.register("catchment-zones", CatchmentZoneViewSet)
router.register("documents", ApplicationDocumentViewSet)

urlpatterns = [path("", include(router.urls))]
