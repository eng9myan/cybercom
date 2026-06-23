import datetime
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Accession, AccessionBatch, AccessionBatchItem, AccessionAudit, AccessionNumberSequence
from .serializers import AccessionSerializer, AccessionBatchSerializer, AccessionBatchItemSerializer, AccessionAuditSerializer
from ..views import LaboratoryModelViewSet

class AccessionViewSet(LaboratoryModelViewSet):
    queryset = Accession.objects.select_related("specimen")
    serializer_class = AccessionSerializer
    required_feature = "lab.accessioning"
    filterset_fields = ["site_code", "status", "is_referred"]
    search_fields = ["accession_number"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        site_code = self.request.data.get("site_code", "HQ")
        year = datetime.date.today().year
        seq, _ = AccessionNumberSequence.objects.get_or_create(
            tenant_id=tenant_id, site_code=site_code, year=year,
            defaults={"prefix": "ACC", "last_sequence": 0}
        )
        accession_number = seq.next_number()
        obj = serializer.save(tenant_id=tenant_id, accession_number=accession_number, accessioned_by=self.request.user.id if self.request.user else None)
        specimen = obj.specimen
        specimen.status = "accessioned"
        specimen.save(update_fields=["status", "updated_at"])
        AccessionAudit.objects.create(tenant_id=tenant_id, accession=obj, event_type="accessioned", detail=f"Accession number assigned: {accession_number}")

class AccessionBatchViewSet(LaboratoryModelViewSet):
    queryset = AccessionBatch.objects.all()
    serializer_class = AccessionBatchSerializer
    required_feature = "lab.accessioning"

class AccessionAuditViewSet(LaboratoryModelViewSet):
    queryset = AccessionAudit.objects.all()
    serializer_class = AccessionAuditSerializer
    required_feature = "lab.accessioning"
    http_method_names = ["get", "head", "options"]
