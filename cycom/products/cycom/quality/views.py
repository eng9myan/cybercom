from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.quality.models import QualityCheckpoint
from products.cycom.quality.serializers import QualityCheckpointSerializer
from products.cycom.quality.services import record_result


class QualityCheckpointViewSet(TenantScopedModelViewSet):
    queryset = QualityCheckpoint.objects.all()
    serializer_class = QualityCheckpointSerializer

    @action(detail=True, methods=["post"], url_path="record-result")
    def record(self, request, pk=None):
        checkpoint = self.get_object()
        result = request.data.get("result")
        if not result:
            raise ValidationError("result is required.")
        claims = getattr(request, "auth_claims", {}) or {}
        checked_by = request.data.get("checked_by", "") or claims.get("email", "")
        record_result(checkpoint, result=result, checked_by=checked_by, notes=request.data.get("notes", ""))
        return Response(QualityCheckpointSerializer(checkpoint).data)
