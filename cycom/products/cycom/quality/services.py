from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.quality.models import QualityCheckpoint


def record_result(checkpoint: QualityCheckpoint, *, result: str, checked_by: str, notes: str = "") -> QualityCheckpoint:
    if result not in ("pass", "fail"):
        raise ValidationError("result must be 'pass' or 'fail'.")
    if checkpoint.result != "pending":
        raise ValidationError(f"Checkpoint already recorded as '{checkpoint.result}'.")
    checkpoint.result = result
    checkpoint.checked_by = checked_by
    checkpoint.checked_at = timezone.now()
    checkpoint.notes = notes
    checkpoint.save(update_fields=["result", "checked_by", "checked_at", "notes", "updated_at"])
    return checkpoint
