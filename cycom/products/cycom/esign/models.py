import secrets

from django.db import models

from platform.common.models import BaseModel


class SignTemplate(BaseModel):
    """A reusable document (PDF) with a field layout (signature/name/date blocks)."""

    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="cycom_esign/templates/%Y/%m/")
    fields_config = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "cycom_esign_templates"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


class SignRequest(BaseModel):
    """One signer's copy of a template, reachable via an unguessable public token."""

    STATUS_CHOICES = [
        ("Sent", "Sent"),
        ("Viewed", "Viewed"),
        ("Signed", "Signed"),
    ]

    template = models.ForeignKey(SignTemplate, on_delete=models.CASCADE, related_name="requests")
    token = models.CharField(max_length=64, unique=True, default=_generate_token, editable=False)
    signers = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Sent")
    signature = models.TextField(blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_esign_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"SignRequest {self.id} ({self.status})"
