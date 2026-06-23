from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.cymed.commercial.partner_management.views import (
    PartnerTypeViewSet, PartnerViewSet,
    ResellerAgreementViewSet, DistributorAgreementViewSet
)

router = DefaultRouter()
router.register("types", PartnerTypeViewSet)
router.register("partners", PartnerViewSet)
router.register("reseller-agreements", ResellerAgreementViewSet)
router.register("distributor-agreements", DistributorAgreementViewSet)

urlpatterns = [path("", include(router.urls))]
