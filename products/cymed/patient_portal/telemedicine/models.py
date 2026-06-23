import uuid
from django.db import models
from platform.common.models import BaseModel


class TelemedicineSession(BaseModel):
    SESSION_TYPE_CHOICES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('chat', 'Chat'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    appointment_request_id = models.UUIDField(null=True, blank=True)
    cymed_telemedicine_id = models.UUIDField(null=True, blank=True)
    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    session_type = models.CharField(
        max_length=20, choices=SESSION_TYPE_CHOICES, default='video'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='scheduled'
    )
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=0)
    meeting_url = models.URLField(max_length=2000, blank=True)
    meeting_id = models.CharField(max_length=255, blank=True)
    meeting_password = models.CharField(max_length=100, blank=True)
    patient_joined_at = models.DateTimeField(null=True, blank=True)
    provider_joined_at = models.DateTimeField(null=True, blank=True)
    chief_complaint = models.TextField(blank=True)
    session_notes_available = models.BooleanField(default=False)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_portal_telemedicine_sessions'
        indexes = [
            models.Index(fields=['account_id', 'status']),
            models.Index(fields=['provider_id', 'scheduled_at']),
        ]

    def __str__(self):
        return f"TelemedicineSession {self.id} - {self.patient_id} [{self.status}]"


class TelemedicineDocument(BaseModel):
    DOCUMENT_TYPE_CHOICES = [
        ('lab_result', 'Lab Result'),
        ('imaging', 'Imaging'),
        ('referral', 'Referral'),
        ('previous_report', 'Previous Report'),
        ('prescription', 'Prescription'),
        ('other', 'Other'),
    ]
    UPLOADED_BY_CHOICES = [
        ('patient', 'Patient'),
        ('provider', 'Provider'),
    ]

    session = models.ForeignKey(
        TelemedicineSession,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    document_type = models.CharField(
        max_length=30, choices=DOCUMENT_TYPE_CHOICES, default='other'
    )
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=2000)
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    file_type = models.CharField(max_length=50)
    uploaded_by = models.CharField(
        max_length=20, choices=UPLOADED_BY_CHOICES, default='patient'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cymed_portal_tele_documents'

    def __str__(self):
        return f"TelemedicineDocument {self.file_name} for session {self.session_id}"


class TelemedicineChat(BaseModel):
    SENDER_TYPE_CHOICES = [
        ('patient', 'Patient'),
        ('provider', 'Provider'),
        ('system', 'System'),
    ]

    session = models.ForeignKey(
        TelemedicineSession,
        on_delete=models.CASCADE,
        related_name='chat_messages',
    )
    sender_type = models.CharField(
        max_length=20, choices=SENDER_TYPE_CHOICES, default='patient'
    )
    sender_id = models.UUIDField()
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_system_message = models.BooleanField(default=False)

    class Meta:
        db_table = 'cymed_portal_tele_chat'
        ordering = ['-sent_at']

    def __str__(self):
        return f"ChatMessage {self.id} in session {self.session_id} by {self.sender_type}"


class TelemedicineRating(BaseModel):
    session = models.OneToOneField(
        TelemedicineSession,
        on_delete=models.CASCADE,
        related_name='session_rating',
    )
    account_id = models.UUIDField(db_index=True)
    overall_rating = models.PositiveSmallIntegerField()
    audio_quality_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    video_quality_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    provider_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    comment = models.TextField(blank=True)
    would_use_again = models.BooleanField(default=True)

    class Meta:
        db_table = 'cymed_portal_tele_ratings'

    def __str__(self):
        return f"TelemedicineRating {self.id} for session {self.session_id} - {self.overall_rating}/5"
