from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.field_service.models import ServiceTask
from products.cycom.field_service.serializers import ServiceTaskSerializer
from products.cycom.field_service.services import complete_worksheet, transition


class ServiceTaskViewSet(TenantScopedModelViewSet):
    queryset = ServiceTask.objects.all()
    serializer_class = ServiceTaskSerializer

    @action(detail=True, methods=["post"], url_path="transition")
    def transition_action(self, request, pk=None):
        new_status = request.data.get("status")
        if not new_status:
            raise ValidationError("status is required.")
        task = transition(self.get_object(), new_status=new_status)
        return Response(ServiceTaskSerializer(task).data)

    @action(detail=True, methods=["post"], url_path="complete-worksheet")
    def complete_worksheet_action(self, request, pk=None):
        task = complete_worksheet(
            self.get_object(),
            notes=request.data.get("notes", ""),
            signature=request.data.get("signature", ""),
        )
        return Response(ServiceTaskSerializer(task).data)
