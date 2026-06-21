"""
Immutable audit log model. ADR-0028: Audit & Legal Record Strategy.
Records are append-only; no update/delete permitted in application layer.
pgAudit handles DDL; this table stores application-level events.
"""
import uuid
from django.db import models
from django.utils import timezone


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    READ = "read", "Read"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    PERMISSION_DENIED = "permission_denied", "Permission Denied"
    BREAK_GLASS = "break_glass", "Break Glass"
    EXPORT = "export", "Data Export"
    IMPORT = "import", "Data Import"


class AuditStatus(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"
    DENIED = "denied", "Denied"


class AuditLog(models.Model):
    """
    Immutable platform audit log. Every sensitive operation emits one row.
    Rows are never updated or deleted by application code.
    A SHA-256 hash chain ensures tamper-evidence (ADR-0028 §5).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=255, blank=True, db_index=True)
    session_id = models.CharField(max_length=255, blank=True)
    trace_id = models.CharField(max_length=64, blank=True, db_index=True)
    action = models.CharField(max_length=30, choices=AuditAction.choices, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=255, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=AuditStatus.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    details = models.JSONField(default=dict, blank=True)
    previous_hash = models.CharField(max_length=64, blank=True)
    entry_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "platform_audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tenant_id", "timestamp"]),
            models.Index(fields=["user_id", "timestamp"]),
            models.Index(fields=["action", "resource_type"]),
        ]

    def __str__(self) -> str:
        return f"AuditLog({self.action}, {self.resource_type}, {self.timestamp})"

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit log entries are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit log entries cannot be deleted.")
