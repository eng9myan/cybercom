from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from platform.cyintegrationhub.models import (
    ConnectorConfig,
    IntegrationPartner,
    MessageAuditLog,
    TransformationMapping,
)
from platform.cyintegrationhub.serializers import (
    ConnectorConfigSerializer,
    ConnectorExecutionRequestSerializer,
    IntegrationPartnerSerializer,
    MessageAuditLogSerializer,
    TransformationMappingSerializer,
)
from platform.cyintegrationhub.services import ConnectorFramework


class IntegrationPartnerViewSet(viewsets.ModelViewSet):
    queryset = IntegrationPartner.objects.all().order_by("name")
    serializer_class = IntegrationPartnerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="execute")
    def execute_connector(self, request, pk=None):
        partner = self.get_object()
        serializer = ConnectorExecutionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        res = ConnectorFramework.execute_connector(
            tenant_id=str(serializer.validated_data["tenant_id"]),
            partner=partner,
            connector_type=serializer.validated_data["connector_type"],
            action=serializer.validated_data["action"],
            payload=serializer.validated_data["payload"],
        )
        return Response(res, status=status.HTTP_200_OK)


class ConnectorConfigViewSet(viewsets.ModelViewSet):
    queryset = ConnectorConfig.objects.all().order_by("name")
    serializer_class = ConnectorConfigSerializer
    permission_classes = [IsAuthenticated]


class TransformationMappingViewSet(viewsets.ModelViewSet):
    queryset = TransformationMapping.objects.all().order_by("name")
    serializer_class = TransformationMappingSerializer
    permission_classes = [IsAuthenticated]


class MessageAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MessageAuditLog.objects.all().order_by("-processed_at")
    serializer_class = MessageAuditLogSerializer
    permission_classes = [IsAuthenticated]
