from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.maintenance.models import MaintenanceRequest


def start_request(req: MaintenanceRequest) -> MaintenanceRequest:
    if req.status != "scheduled":
        raise ValidationError(f"Request must be 'scheduled' to start, is '{req.status}'.")
    req.status = "in_progress"
    req.started_at = timezone.now()
    req.save(update_fields=["status", "started_at", "updated_at"])
    return req


def complete_request(req: MaintenanceRequest) -> MaintenanceRequest:
    if req.status != "in_progress":
        raise ValidationError(f"Request must be 'in_progress' to complete, is '{req.status}'.")
    req.completed_at = timezone.now()
    if req.started_at:
        delta = req.completed_at - req.started_at
        req.downtime_hours = round(delta.total_seconds() / 3600, 2)
    req.status = "done"
    req.save(update_fields=["status", "completed_at", "downtime_hours", "updated_at"])
    return req
