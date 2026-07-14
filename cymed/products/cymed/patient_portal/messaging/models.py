from django.db import models

from platform.common.models import BaseModel


class MessageThread(BaseModel):
    THREAD_TYPE_CHOICES = [
        ("provider_message", "Provider Message"),
        ("appointment_inquiry", "Appointment Inquiry"),
        ("prescription_inquiry", "Prescription Inquiry"),
        ("lab_inquiry", "Lab Inquiry"),
        ("billing_inquiry", "Billing Inquiry"),
        ("support", "Support"),
        ("general", "General"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
        ("archived", "Archived"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    thread_type = models.CharField(max_length=30, choices=THREAD_TYPE_CHOICES, default="general")
    subject = models.CharField(max_length=255)
    provider_id = models.UUIDField(null=True, blank=True)
    provider_name = models.CharField(max_length=255, blank=True)
    facility_id = models.UUIDField(null=True, blank=True)
    facility_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    is_urgent = models.BooleanField(default=False)
    last_message_at = models.DateTimeField(null=True, blank=True)
    message_count = models.PositiveIntegerField(default=0)
    unread_count = models.PositiveIntegerField(default=0)
    cyconnect_thread_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_portal_message_threads"
        indexes = [
            models.Index(fields=["account_id", "status", "last_message_at"]),
        ]

    def __str__(self):
        return f"Thread: {self.subject} ({self.status})"


class PatientMessage(BaseModel):
    SENDER_TYPE_CHOICES = [
        ("patient", "Patient"),
        ("provider", "Provider"),
        ("system", "System"),
    ]

    thread = models.ForeignKey(
        MessageThread,
        related_name="messages",
        on_delete=models.CASCADE,
    )
    account_id = models.UUIDField(db_index=True)
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE_CHOICES, default="patient")
    sender_id = models.UUIDField()
    sender_name = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_system_message = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_portal_messages"
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["thread", "is_read"]),
        ]

    def __str__(self):
        return f"Message from {self.sender_name} in thread {self.thread_id}"


class MessageAttachment(BaseModel):
    message = models.ForeignKey(
        PatientMessage,
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    account_id = models.UUIDField(db_index=True)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=2000)
    file_type = models.CharField(max_length=50)
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_portal_message_attachments"

    def __str__(self):
        return f"Attachment: {self.file_name}"


class SecureMessageRecipient(BaseModel):
    RECIPIENT_TYPE_CHOICES = [
        ("patient", "Patient"),
        ("provider", "Provider"),
        ("support_team", "Support Team"),
    ]

    thread = models.ForeignKey(
        MessageThread,
        related_name="recipients",
        on_delete=models.CASCADE,
    )
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPE_CHOICES)
    recipient_id = models.UUIDField(db_index=True)
    recipient_name = models.CharField(max_length=255, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_portal_message_recipients"
        indexes = [
            models.Index(fields=["thread", "recipient_id"]),
        ]

    def __str__(self):
        return f"Recipient {self.recipient_name} ({self.recipient_type})"
