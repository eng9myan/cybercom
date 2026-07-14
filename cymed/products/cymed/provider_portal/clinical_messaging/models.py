from django.db import models

from platform.common.models import BaseModel


class ThreadType(models.TextChoices):
    DIRECT = "direct", "Direct"
    TEAM = "team", "Team"
    PATIENT_DISCUSSION = "patient_discussion", "Patient Discussion"
    HANDOFF = "handoff", "Handoff"
    CONSULT_REQUEST = "consult_request", "Consult Request"
    ESCALATION = "escalation", "Escalation"
    CLINICAL_GROUP = "clinical_group", "Clinical Group"


class ThreadStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
    RESOLVED = "resolved", "Resolved"


class MessagePriority(models.TextChoices):
    ROUTINE = "routine", "Routine"
    URGENT = "urgent", "Urgent"
    STAT = "stat", "STAT"


class AttachmentType(models.TextChoices):
    LAB_RESULT = "lab_result", "Lab Result"
    IMAGING = "imaging", "Imaging"
    DOCUMENT = "document", "Document"
    PHOTO = "photo", "Photo"
    OTHER = "other", "Other"


class GroupType(models.TextChoices):
    DEPARTMENT = "department", "Department"
    UNIT = "unit", "Unit"
    SPECIALTY = "specialty", "Specialty"
    ON_CALL = "on_call", "On Call"
    COMMITTEE = "committee", "Committee"
    AD_HOC = "ad_hoc", "Ad Hoc"


class ClinicalMessageThread(BaseModel):
    thread_type = models.CharField(max_length=30, choices=ThreadType.choices)
    subject = models.CharField(max_length=500, blank=True)
    patient_id = models.UUIDField(db_index=True, null=True, blank=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ThreadStatus.choices,
        default=ThreadStatus.ACTIVE,
    )
    is_urgent = models.BooleanField(default=False)
    is_encrypted = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    unread_count = models.PositiveIntegerField(default=0)
    cyconnect_thread_id = models.UUIDField(null=True, blank=True)
    created_by_provider_id = models.UUIDField()

    class Meta:
        db_table = "cymed_prov_msg_threads"
        ordering = ["-last_message_at"]

    def __str__(self):
        return f"Thread({self.thread_type} / {self.subject[:50]})"


class ClinicalMessage(BaseModel):
    thread = models.ForeignKey(
        ClinicalMessageThread,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_provider_id = models.UUIDField(db_index=True)
    sender_name = models.CharField(max_length=255)
    sender_type = models.CharField(max_length=50)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_system_message = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=20,
        choices=MessagePriority.choices,
        default=MessagePriority.ROUTINE,
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_prov_messages"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Message(thread={self.thread_id} from={self.sender_name})"


class MessageAttachment(BaseModel):
    message = models.ForeignKey(
        ClinicalMessage,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file_name = models.CharField(max_length=500)
    file_url = models.URLField(max_length=2000)
    file_type = models.CharField(max_length=100)
    file_size_bytes = models.PositiveIntegerField()
    attachment_type = models.CharField(
        max_length=30,
        choices=AttachmentType.choices,
        default=AttachmentType.OTHER,
    )
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cymed_prov_msg_attachments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Attachment({self.file_name})"


class ClinicalGroup(BaseModel):
    name = models.CharField(max_length=255)
    group_type = models.CharField(max_length=30, choices=GroupType.choices)
    description = models.TextField(blank=True)
    members = models.JSONField(default=list)
    admin_provider_id = models.UUIDField()
    is_active = models.BooleanField(default=True)
    message_retention_days = models.PositiveIntegerField(default=365)

    class Meta:
        db_table = "cymed_prov_clinical_groups"
        ordering = ["name"]

    def __str__(self):
        return f"ClinicalGroup({self.name} / {self.group_type})"


class MessageThreadParticipant(BaseModel):
    thread = models.ForeignKey(
        ClinicalMessageThread,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_msg_participants"
        ordering = ["joined_at"]

    def __str__(self):
        return f"Participant({self.provider_name} in thread={self.thread_id})"
