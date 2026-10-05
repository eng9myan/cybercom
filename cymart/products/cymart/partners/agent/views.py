import logging

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from django.utils.module_loading import import_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import schema  # noqa: F401
from ..auth import PartnerAPIKeyAuthentication
from ..models import PartnerCallLog
from ..throttle import AgentRateThrottle, PartnerRateThrottle
from .orchestrator import AgentOrchestrator
from .serializers import AgentTurnRequestSerializer

log = logging.getLogger(__name__)


def load_provider():
    return import_string(settings.AGENT_PROVIDER)()


class PartnerAgentTurnView(APIView):
    """One turn of the ordering agent. The platform sends the transcript and the
    customer's plan; it gets back a reply, a platform tool to run, or a confirmation to obtain."""

    authentication_classes = [PartnerAPIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [PartnerRateThrottle, AgentRateThrottle]

    @extend_schema(request=AgentTurnRequestSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT},
                   summary="One turn of the ordering assistant",
                   description="Send the transcript and the customer's plan. The reply is text, ONE platform tool for your app to run, or a confirmation for the customer to approve. Stateless: you keep the transcript. A meal-time trigger can start a conversation.")
    def post(self, request):
        serializer = AgentTurnRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        messages = [self._plain(m) for m in data["messages"]]
        try:
            result = AgentOrchestrator(load_provider(), data["language"]).run(
                data["profile"], messages, data["platform_tools"], data["confirmed"], data.get("trigger")
            )
        except Exception as exc:  # the provider (model API) failed; never leak its message
            log.error("agent provider failed: %s", type(exc).__name__)
            return Response({"error": "agent_unavailable", "detail": "The assistant is temporarily unavailable."}, status=503)

        PartnerCallLog.objects.create(partner=request.partner, item_count=min(result.steps, 32000))
        return Response({
            "language": data["language"],
            "status": result.status,
            "reply": result.reply,
            "tool_calls": result.tool_calls,
            "confirmation": result.confirmation,
            "new_messages": result.new_messages,
            "events": result.events,
            "steps": result.steps,
        })

    @staticmethod
    def _plain(m) -> dict:
        out = {"role": m["role"], "content": m.get("content")}
        if m.get("tool_calls"):
            out["tool_calls"] = [{"id": c["id"], "name": c["name"], "arguments": dict(c.get("arguments") or {})} for c in m["tool_calls"]]
        for k in ("tool_call_id", "name"):
            if m.get(k):
                out[k] = m[k]
        return out
