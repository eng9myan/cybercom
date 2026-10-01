from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.hr.imports import run_import
from products.cycom.hr.models import Contract, Department, Employee, EmployeeDocument, EmployeeInsurance
from products.cycom.hr.serializers import (
    DepartmentSerializer,
    build_department_tree,
    ContractSerializer,
    EmployeeDocumentSerializer,
    EmployeeInsuranceSerializer,
    EmployeeSerializer,
)


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


class EmployeeDocumentViewSet(TenantScopedModelViewSet):
    queryset = EmployeeDocument.objects.select_related("employee").all()
    serializer_class = EmployeeDocumentSerializer
    filterset_fields = ["employee", "document_type"]


class EmployeeInsuranceViewSet(TenantScopedModelViewSet):
    queryset = EmployeeInsurance.objects.select_related("employee").all()
    serializer_class = EmployeeInsuranceSerializer
    filterset_fields = ["employee", "status"]


class DepartmentViewSet(TenantScopedModelViewSet):
    """Department tree. Bare-array list (a tenant's org chart is bounded and
    the page renders it whole). Deleting a unit that still has
    sub-departments or members is refused rather than orphaning them."""

    queryset = Department.objects.select_related("parent", "manager").all()
    serializer_class = DepartmentSerializer
    pagination_class = None

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if getattr(self.request, "tenant_id", None):
            ctx["department_tree"] = build_department_tree(self.request.tenant_id)
        return ctx

    def destroy(self, request, *args, **kwargs):
        dept = self.get_object()
        if dept.children.exists():
            return Response({"detail": "Move or delete its sub-departments first."}, status=400)
        if dept.members.exclude(status="terminated").exists():
            return Response({"detail": "Reassign its employees first."}, status=400)
        return super().destroy(request, *args, **kwargs)
