from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cymed.commercial.partner_management.views import (
    DistributorAgreementViewSet,
    PartnerTypeViewSet,
    PartnerViewSet,
    ResellerAgreementViewSet,
)

router = DefaultRouter()
router.register("types", PartnerTypeViewSet)
router.register("partners", PartnerViewSet)
router.register("reseller-agreements", ResellerAgreementViewSet)
router.register("distributor-agreements", DistributorAgreementViewSet)

urlpatterns = [path("", include(router.urls))]
