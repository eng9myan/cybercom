from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.leave.models import LeaveRequest, LeaveType
from products.cycom.leave.serializers import LeaveRequestSerializer, LeaveTypeSerializer
from products.cycom.leave.services import leave_balance, validate_approvable


class LeaveTypeViewSet(TenantScopedModelViewSet):
    queryset = LeaveType.objects.filter(is_active=True)
    serializer_class = LeaveTypeSerializer


class LeaveRequestViewSet(TenantScopedModelViewSet):
    queryset = LeaveRequest.objects.select_related("employee", "leave_type").all()
    serializer_class = LeaveRequestSerializer
    filterset_fields = ["status", "employee", "leave_type"]

    def perform_create(self, serializer):
        obj = serializer.save(tenant_id=self.request.tenant_id)
        obj.days = obj.compute_days()
        obj.save(update_fields=["days"])

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        req = self.get_object()
        if req.status != "draft":
            raise ValidationError(f"Request is '{req.status}', cannot submit.")
        req.status = "submitted"
        req.save(update_fields=["status"])
        return Response(LeaveRequestSerializer(req).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        req = self.get_object()
        if req.status != "submitted":
            raise ValidationError(f"Request is '{req.status}', not awaiting approval.")
        validate_approvable(req)
        req.status = "approved"
        req.approved_by = getattr(request, "user_session", {}).get("email", "")
        req.save(update_fields=["status", "approved_by"])
        return Response(LeaveRequestSerializer(req).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        req = self.get_object()
        if req.status != "submitted":
            raise ValidationError(f"Request is '{req.status}', not awaiting approval.")
        req.status = "rejected"
        req.rejection_reason = request.data.get("reason", "")
        req.save(update_fields=["status", "rejection_reason"])
        return Response(LeaveRequestSerializer(req).data)

    @action(detail=False, methods=["get"])
    def balance(self, request):
        """?employee=<id>&leave_type=<id>&year=<yyyy> → allocation/taken/remaining."""
        emp = request.query_params.get("employee")
        lt_id = request.query_params.get("leave_type")
        if not (emp and lt_id):
            raise ValidationError("employee and leave_type query params are required.")
        lt = LeaveType.objects.filter(tenant_id=request.tenant_id, id=lt_id).first()
        if not lt:
            raise ValidationError("leave_type not found.")
        year = request.query_params.get("year")
        return Response(leave_balance(request.tenant_id, emp, lt, year=int(year) if year else None))
