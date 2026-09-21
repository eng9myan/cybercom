from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.appraisals.models import Appraisal
from products.cycom.appraisals.serializers import AppraisalSerializer


class AppraisalViewSet(TenantScopedModelViewSet):
    queryset = Appraisal.objects.select_related("employee").all()
    serializer_class = AppraisalSerializer
    filterset_fields = ["employee", "status"]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        appraisal = self.get_object()
        if appraisal.rating is None:
            raise ValidationError("Cannot complete an appraisal with no rating.")
        appraisal.status = "completed"
        appraisal.completed_at = timezone.now()
        appraisal.save(update_fields=["status", "completed_at", "updated_at"])
        return Response(self.get_serializer(appraisal).data)
