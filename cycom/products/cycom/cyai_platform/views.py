from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.cyai_platform.models import AgentDefinition, AgentEntitlement
from products.cycom.cyai_platform.serializers import AgentDefinitionSerializer, AgentEntitlementSerializer
from products.cycom.cyai_platform.services import has_active_entitlement, route_question


class AgentListView(APIView):
    """Foundation for the future AI Center UI: the 3 agents plus the
    caller's own entitlement status for each."""

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        agents = AgentDefinition.objects.filter(is_active=True)
        data = []
        for agent in agents:
            entry = AgentDefinitionSerializer(agent).data
            entry["entitled"] = (
                tenant_id is None or has_active_entitlement(tenant_id, agent.agent_key)
            )
            data.append(entry)
        return Response(data)


class RouteQuestionView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def post(self, request):
        question = request.data.get("question", "")
        return Response(route_question(question))


class AgentEntitlementViewSet(TenantScopedModelViewSet):
    """Granting/revoking agent access is itself a privileged action —
    platform-admin-only, matching the access-grant pattern used elsewhere."""

    queryset = AgentEntitlement.objects.select_related("agent").all()
    serializer_class = AgentEntitlementSerializer
    permission_classes = [IsPlatformAdmin]
