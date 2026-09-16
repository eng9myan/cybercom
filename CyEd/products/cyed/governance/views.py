from django.utils import timezone
from rest_framework import mixins, viewsets

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff
from products.cyed.governance.models import AuditEvent, ConsentRecord
from products.cyed.governance.serializers import AuditEventSerializer, ConsentRecordSerializer


class AuditEventViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only, staff-only audit log. No create/update/delete (append-only)."""

    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is not None:
            qs = qs.filter(tenant_id=tenant_id)
        params = self.request.query_params
        model_label = params.get("model_label")
        object_id = params.get("object_id")
        if model_label:
            qs = qs.filter(model_label=model_label)
        if object_id:
            qs = qs.filter(object_id=object_id)
        return qs


class ConsentRecordViewSet(TenantScopedModelViewSet):
    """Consent records — staff manage; the AI consent gate reads these."""

    queryset = ConsentRecord.objects.select_related("student").all()
    serializer_class = ConsentRecordSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        student = self.request.query_params.get("student")
        consent_type = self.request.query_params.get("consent_type")
        if student:
            qs = qs.filter(student_id=student)
        if consent_type:
            qs = qs.filter(consent_type=consent_type)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, decided_at=timezone.now())

    def perform_update(self, serializer):
        serializer.save(decided_at=timezone.now())
