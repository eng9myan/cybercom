from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff, has_any, PASTORAL_OR_LEADERSHIP
from products.cyed.meetings.models import MeetingSession
from products.cyed.meetings.serializers import MeetingSessionSerializer
from products.cyed.meetings import stt, summarise


class MeetingSessionViewSet(TenantScopedModelViewSet):
    """
    Create with a `transcript` (from client/device STT) or an `audio` file (STT
    seam). Summary + action items computed on save. Confidential (counselling)
    sessions are readable by pastoral/leadership only.
    """

    queryset = MeetingSession.objects.select_related("student").all()
    serializer_class = MeetingSessionSerializer
    permission_classes = [IsStaff]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = super().get_queryset()
        # Non-pastoral staff cannot see confidential counselling notes.
        if not has_any(self.request, PASTORAL_OR_LEADERSHIP):
            qs = qs.filter(is_confidential=False)
        mtype = self.request.query_params.get("meeting_type")
        if mtype:
            qs = qs.filter(meeting_type=mtype)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(tenant_id=self.request.tenant_id)
        transcript = instance.transcript
        audio = self.request.FILES.get("audio")
        if audio is not None and not transcript:
            got = stt.transcribe(audio.read(), getattr(audio, "content_type", ""))
            if got:
                transcript = got
                instance.transcript = got
        result = summarise.summarise(transcript)
        instance.summary = result["summary"]
        instance.action_items = result["action_items"]
        instance.key_points = result["key_points"]
        instance.status = "summarised" if transcript else "draft"
        instance.save()

    @action(detail=True, methods=["post"])
    def summarise(self, request, pk=None):
        session = self.get_object()
        result = summarise.summarise(session.transcript)
        session.summary = result["summary"]
        session.action_items = result["action_items"]
        session.key_points = result["key_points"]
        session.status = "summarised"
        session.save(update_fields=["summary", "action_items", "key_points", "status", "updated_at"])
        return Response(self.get_serializer(session).data)
