from core.viewsets import TenantScopedModelViewSet
from products.cycom.recruitment.models import Applicant
from products.cycom.recruitment.serializers import ApplicantSerializer


class ApplicantViewSet(TenantScopedModelViewSet):
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer
    filterset_fields = ["stage", "job_title"]
