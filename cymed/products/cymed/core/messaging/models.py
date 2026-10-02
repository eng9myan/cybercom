"""
Secure patient ↔ care-team messaging.

A thread belongs to one patient inside one tenant. Staff of that tenant see
every thread; a patient sees only threads about themselves. Message bodies
are PHI and stored encrypted per tenant.
"""
from django.db import models
from django.utils import timezone

from platform.common.fields import EncryptedText
from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient


class MessageThread(BaseModel):
    CATEGORIES = [
        ("general", "General question"),
        ("prescription", "Prescription / refill"),
        ("results", "Test results"),
        ("appointment", "Appointment"),
        ("billing", "Billing"),
    ]
    STATUS = [("open", "Open"), ("closed", "Closed")]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="message_threads")
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="general")
    status = models.CharField(max_length=10, choices=STATUS, default="open", db_index=True)
    # Care-team member or pool ("cardiology-nurses") the thread is routed to.
    assigned_to = models.CharField(max_length=255, blank=True, db_index=True)
    last_message_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "cymed_message_threads"
        ordering = ["-last_message_at"]

    def __str__(self) -> str:
        return f"Thread({self.subject})"


class Message(BaseModel):
    SENDERS = [("patient", "Patient"), ("staff", "Care team")]

    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")
    sender_type = models.CharField(max_length=10, choices=SENDERS)
    sender = models.CharField(max_length=255)  # email / user id of the author
    body = EncryptedText(classification="phi")
    read_at = models.DateTimeField(null=True, blank=True)  # by the other side

    class Meta:
        db_table = "cymed_messages"
        ordering = ["created_at"]
