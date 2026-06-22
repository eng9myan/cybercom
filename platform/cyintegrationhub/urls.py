from django.urls import path, include
from rest_framework.routers import DefaultRouter
from platform.cyintegrationhub.views import (
    IntegrationPartnerViewSet,
    ConnectorConfigViewSet,
    TransformationMappingViewSet,
    MessageAuditLogViewSet
)

router = DefaultRouter()
router.register("partners", IntegrationPartnerViewSet, basename="integration-partner")
router.register("configs", ConnectorConfigViewSet, basename="connector-config")
router.register("mappings", TransformationMappingViewSet, basename="transformation-mapping")
router.register("message-audits", MessageAuditLogViewSet, basename="message-audit")

urlpatterns = [
    path("", include(router.urls)),
]
