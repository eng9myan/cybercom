from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.field_service.models import ServiceTask

VALID_TRANSITIONS = {
    "scheduled": {"en_route", "cancelled"},
    "en_route": {"in_progress", "cancelled"},
    "in_progress": {"done", "cancelled"},
}


def transition(task: ServiceTask, *, new_status: str) -> ServiceTask:
    allowed = VALID_TRANSITIONS.get(task.status, set())
    if new_status not in allowed:
        raise ValidationError(f"Cannot move from '{task.status}' to '{new_status}'.")
    task.status = new_status
    if new_status == "done":
        task.completed_at = timezone.now()
    task.save(update_fields=["status", "completed_at", "updated_at"])
    return task


def complete_worksheet(task: ServiceTask, *, notes: str, signature: str = "") -> ServiceTask:
    if task.status != "in_progress":
        raise ValidationError(f"Task must be 'in_progress' to complete worksheet, is '{task.status}'.")
    task.worksheet_notes = notes
    task.customer_signature = signature
    task.status = "done"
    task.completed_at = timezone.now()
    task.save(
        update_fields=["worksheet_notes", "customer_signature", "status", "completed_at", "updated_at"]
    )
    return task
