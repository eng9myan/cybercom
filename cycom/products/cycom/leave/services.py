"""Leave balance + approval validation."""

from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from rest_framework.exceptions import ValidationError

from products.cycom.leave.models import LeaveRequest


def leave_balance(tenant_id, employee_id, leave_type, year=None):
    """allocated (from the type) − approved days taken this year = remaining."""
    year = year or date.today().year
    allocated = leave_type.days_per_year
    taken = (
        LeaveRequest.objects.filter(
            tenant_id=tenant_id, employee_id=employee_id, leave_type=leave_type,
            status="approved", start_date__year=year,
        ).aggregate(t=Sum("days"))["t"]
        or Decimal("0")
    )
    return {
        "leave_type": leave_type.code,
        "leave_type_name": leave_type.name,
        "year": year,
        "allocated": allocated,
        "taken": taken,
        "remaining": allocated - taken,
    }


def validate_approvable(request: LeaveRequest):
    """Reject overlaps and (for paid leave) over-allocation before approving."""
    overlap = LeaveRequest.objects.filter(
        tenant_id=request.tenant_id, employee=request.employee, status="approved",
    ).exclude(id=request.id).filter(
        Q(start_date__lte=request.end_date) & Q(end_date__gte=request.start_date)
    )
    if overlap.exists():
        raise ValidationError("Overlaps an already-approved leave for this employee.")

    if request.leave_type.is_paid and request.leave_type.days_per_year > 0:
        bal = leave_balance(
            request.tenant_id, request.employee_id, request.leave_type,
            year=request.start_date.year,
        )
        if request.days > bal["remaining"]:
            raise ValidationError(
                f"Insufficient balance: requesting {request.days}d, "
                f"only {bal['remaining']}d of {request.leave_type.name} remain."
            )
