from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.hr.imports import run_import
from products.cycom.hr.models import Contract, Employee
from products.cycom.hr.serializers import ContractSerializer, EmployeeSerializer


class EmployeeViewSet(TenantScopedModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    @action(detail=False, methods=["post"], url_path="bulk-import")
    def bulk_import(self, request):
        """
        Bulk employee import with server-side validation.
        Body: {"rows": [...], "dry_run": bool}. dry_run validates without
        writing; a real run creates valid rows and skips invalid ones.
        """
        rows = request.data.get("rows")
        if not isinstance(rows, list):
            return Response({"detail": "Body must include a 'rows' array."}, status=400)
        dry_run = bool(request.data.get("dry_run", False))
        return Response(run_import(rows, request.tenant_id, dry_run=dry_run))


class ContractViewSet(TenantScopedModelViewSet):
    queryset = Contract.objects.select_related("employee").all()
    serializer_class = ContractSerializer
