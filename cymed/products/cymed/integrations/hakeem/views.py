from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .client import HakeemClient
from .models import HakeemMessage
from .serializers import HakeemMessageSerializer


class HakeemMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HakeemMessage.objects.all()
    serializer_class = HakeemMessageSerializer


class HakeemLookupView(APIView):
    """POST { national_id } → { patient, meds, labs } — orchestrates 3 pulls."""

    def post(self, request):
        nid = request.data.get("national_id", "").strip()
        if not nid:
            return Response({"detail": "national_id required"}, status=400)
        c = HakeemClient()
        return Response({
            "patient": c.get_patient(nid),
            "meds": c.get_active_meds(nid),
            "labs": c.get_lab_results(nid),
        })
