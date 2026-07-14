from django.urls import include, path
from rest_framework.routers import DefaultRouter

from platform.cyintegrationhub.views import (
    ConnectorConfigViewSet,
    IntegrationPartnerViewSet,
    MessageAuditLogViewSet,
    TransformationMappingViewSet,
)

router = DefaultRouter()
router.register("partners", IntegrationPartnerViewSet, basename="integration-partner")
router.register("configs", ConnectorConfigViewSet, basename="connector-config")
router.register("mappings", TransformationMappingViewSet, basename="transformation-mapping")
router.register("message-audits", MessageAuditLogViewSet, basename="message-audit")

urlpatterns = [
    path("", include(router.urls)),
]
