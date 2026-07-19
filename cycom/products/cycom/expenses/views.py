from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from platform.tenant.permissions import IsPlatformAdmin

from core.viewsets import TenantScopedModelViewSet
from products.cycom.expenses.models import Expense
from products.cycom.expenses.serializers import ExpenseSerializer
from products.cycom.expenses.services import (
    ExpenseStateError,
    approve_and_post_expense,
    reject_expense,
)


class ExpenseViewSet(TenantScopedModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        expense = self.get_object()
        if expense.status != "draft":
            raise ValidationError(f"Expense must be 'draft' to submit, is '{expense.status}'.")
        expense.status = "submitted"
        expense.save(update_fields=["status", "updated_at"])
        return Response(ExpenseSerializer(expense).data)

    @action(
        detail=True, methods=["post"], url_path="approve", permission_classes=[IsPlatformAdmin]
    )
    def approve(self, request, pk=None):
        expense = self.get_object()
        claims = getattr(request, "auth_claims", {}) or {}
        approved_by = request.data.get("approved_by", "") or claims.get("email", "")
        try:
            approve_and_post_expense(expense, approved_by=approved_by)
        except ExpenseStateError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(ExpenseSerializer(expense).data)

    @action(
        detail=True, methods=["post"], url_path="reject", permission_classes=[IsPlatformAdmin]
    )
    def reject(self, request, pk=None):
        expense = self.get_object()
        try:
            reject_expense(expense, reason=request.data.get("reason", ""))
        except ExpenseStateError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(ExpenseSerializer(expense).data)
