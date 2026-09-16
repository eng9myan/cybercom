"""
E-signature workflow for staff contracts, permission slips, and parent consent
forms, with a tamper-evident audit trail.

Design notes:
  - The document body is hashed (SHA-256) when it is *sent*. Each signature
    stores the hash it signed against, so editing the body after signing is
    detectable (`verify()`), mirroring the report-card document pattern.
  - `SignatureAuditEvent` is append-only: every send/view/sign/decline/void is
    recorded with actor, timestamp, and IP. Nothing in this app deletes it.
"""

import hashlib

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


def content_hash_of(title: str, body: str) -> str:
    return hashlib.sha256(f"{title}\n---\n{body}".encode("utf-8")).hexdigest()


class SignableDocument(BaseModel):
    DOC_TYPES = [
        ("staff_contract", "Staff Contract"),
        ("permission_slip", "Excursion Permission Slip"),
        ("consent_form", "Parent Consent Form"),
        ("policy", "Policy Acknowledgement"),
        ("other", "Other"),
    ]
    STATUS = [
        ("draft", "Draft"),
        ("sent", "Sent for Signature"),
        ("partially_signed", "Partially Signed"),
        ("completed", "Completed"),
        ("declined", "Declined"),
        ("voided", "Voided"),
    ]

    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES, default="other")
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    created_by = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, blank=True)  # sealed at send time

    # Optional links so a document can be traced back to its subject.
    # `documents` is already taken on Student by cyed_intake.DocumentIntake.
    staff = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True, related_name="signable_documents"
    )
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.SET_NULL, null=True, blank=True, related_name="signable_documents"
    )

    class Meta:
        db_table = "cyed_signable_documents"
        ordering = ["-created_at"]

    # ── state ────────────────────────────────────────────────────────────────
    @property
    def signed_count(self) -> int:
        return self.signatories.filter(status="signed").count()

    @property
    def pending_count(self) -> int:
        return self.signatories.filter(status="pending").count()

    def verify(self) -> bool:
        """False if the body changed after the document was sealed."""
        if not self.content_hash:
            return True  # never sent — nothing sealed yet
        return content_hash_of(self.title, self.body) == self.content_hash

    def refresh_status(self):
        total = self.signatories.count()
        signed = self.signed_count
        if self.signatories.filter(status="declined").exists():
            self.status = "declined"
        elif total and signed == total:
            self.status = "completed"
            self.completed_at = self.completed_at or timezone.now()
        elif signed:
            self.status = "partially_signed"
        self.save()
        return self

    def __str__(self):
        return f"{self.title} ({self.status})"


class Signatory(BaseModel):
    """One party who must sign. Order supports sequential signing."""

    ROLES = [("staff", "Staff"), ("parent", "Parent/Guardian"), ("student", "Student"), ("other", "Other")]
    STATUS = [("pending", "Pending"), ("signed", "Signed"), ("declined", "Declined")]

    document = models.ForeignKey(SignableDocument, on_delete=models.CASCADE, related_name="signatories")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLES, default="other")
    order = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    signed_at = models.DateTimeField(null=True, blank=True)
    typed_signature = models.CharField(max_length=255, blank=True)
    signed_hash = models.CharField(max_length=64, blank=True)  # hash of what they signed
    ip_address = models.CharField(max_length=64, blank=True)
    decline_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_document_signatories"
        ordering = ["order", "created_at"]
        constraints = [
            models.UniqueConstraint(fields=["document", "email"], name="uniq_signatory_per_document")
        ]

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.status}"


class SignatureAuditEvent(BaseModel):
    """Append-only trail. Never updated or deleted by application code."""

    ACTIONS = [
        ("created", "Created"), ("sent", "Sent"), ("viewed", "Viewed"),
        ("signed", "Signed"), ("declined", "Declined"), ("voided", "Voided"),
        ("reminded", "Reminder Sent"),
    ]

    document = models.ForeignKey(SignableDocument, on_delete=models.CASCADE, related_name="audit_events")
    signatory = models.ForeignKey(
        Signatory, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events"
    )
    action = models.CharField(max_length=20, choices=ACTIONS)
    actor = models.CharField(max_length=255, blank=True)
    detail = models.CharField(max_length=500, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "cyed_signature_audit_events"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.action} by {self.actor} @ {self.created_at}"


def write_signature_audit(document, action, actor="", detail="", signatory=None, ip=""):
    SignatureAuditEvent.objects.create(
        tenant_id=document.tenant_id, document=document, signatory=signatory,
        action=action, actor=actor, detail=detail[:500], ip_address=ip,
    )
