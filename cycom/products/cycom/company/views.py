from core.viewsets import TenantScopedModelViewSet
from products.cycom.company.models import Company
from products.cycom.company.serializers import CompanySerializer


class CompanyViewSet(TenantScopedModelViewSet):
    queryset = Company.objects.select_related("parent_company").all()
    serializer_class = CompanySerializer
    filterset_fields = ["is_active", "parent_company"]
