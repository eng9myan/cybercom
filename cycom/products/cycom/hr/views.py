from core.viewsets import TenantScopedModelViewSet
from products.cycom.hr.models import Contract, Employee
from products.cycom.hr.serializers import ContractSerializer, EmployeeSerializer


class EmployeeViewSet(TenantScopedModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class ContractViewSet(TenantScopedModelViewSet):
    queryset = Contract.objects.select_related("employee").all()
    serializer_class = ContractSerializer
