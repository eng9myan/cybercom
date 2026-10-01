from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .orchestrator import AgentSession
from .serializers import AgentMessageRequestSerializer, AgentReplySerializer


class AgentMessageView(APIView):
    """The single entry point for the CyMart voice/chat agent. A voice
    client transcribes speech to text (STT) before calling this, and
    speaks the ``reply`` back (TTS) — this endpoint itself is
    modality-agnostic."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AgentMessageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer_id = request.user_session["user_id"]
        result = AgentSession().handle(customer_id, serializer.validated_data["text"])
        return Response(AgentReplySerializer(result).data)
