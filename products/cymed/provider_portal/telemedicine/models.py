import uuid
from django.db import models
from platform.common.models import BaseModel


class ProviderTelemedicineSession(BaseModel):
    SESSION_TYPE_CHOICES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('chat', 'Chat'),
    ]
    VISIT_TYPE_CHOICES = [
        ('follow_up', 'Follow Up'),
        ('consultation', 'Consultation'),
        ('second_opinion', 'Second Opinion'),
        ('remote_monitoring', 'Remote Monitoring'),
        ('virtual_round', 'Virtual Round'),
        ('triage', 'Triage'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]

    patient_id = models.UUIDField(db_index=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=100)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='video')
    visit_type = models.CharField(max_length=30, choices=VISIT_TYPE_CHOICES, default='follow_up')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    scheduled_at = models.DateTimeField()
    patient_joined_at = models.DateTimeField(null=True, blank=True)
    provider_joined_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    meeting_url = models.URLField(blank=True)
    meeting_id = models.CharField(max_length=255, blank=True)
    meeting_password = models.CharField(max_length=255, blank=True)
    cymed_patient_session_id = models.UUIDField(null=True, blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    session_summary = models.TextField(blank=True)
    ai_session_summary = models.TextField(blank=True)

    class Meta:
        db_table = 'cymed_prov_tele_sessions'

    def __str__(self):
        return f"Session {self.id} for patient {self.patient_id} ({self.status})"


class ConsultRequest(BaseModel):
    URGENCY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]

    patient_id = models.UUIDField(db_index=True)
    requesting_provider_id = models.UUIDField(db_index=True)
    requesting_provider_name = models.CharField(max_length=255)
    consulting_provider_id = models.UUIDField(db_index=True, null=True, blank=True)
    consulting_specialty = models.CharField(max_length=100)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='routine')
    consult_reason = models.TextField()
    relevant_history = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    consult_note_id = models.UUIDField(null=True, blank=True)
    response_summary = models.TextField(blank=True)
    is_telemedicine = models.BooleanField(default=False)
    tele_session_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_prov_consult_requests'

    def __str__(self):
        return f"Consult for patient {self.patient_id} ({self.consulting_specialty}) - {self.status}"


class SecondOpinionRequest(BaseModel):
    URGENCY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
        ('cancelled', 'Cancelled'),
    ]

    patient_id = models.UUIDField(db_index=True)
    requesting_provider_id = models.UUIDField()
    requested_specialist_id = models.UUIDField(null=True, blank=True)
    requested_specialty = models.CharField(max_length=100)
    clinical_question = models.TextField()
    attached_records = models.JSONField(default=list)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='routine')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    opinion_text = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_prov_second_opinions'

    def __str__(self):
        return f"Second opinion for patient {self.patient_id} ({self.requested_specialty}) - {self.status}"


class TelemedicineDocument(BaseModel):
    DOCUMENT_TYPE_CHOICES = [
        ('lab_result', 'Lab Result'),
        ('imaging', 'Imaging'),
        ('prescription', 'Prescription'),
        ('referral', 'Referral'),
        ('consent', 'Consent'),
        ('previous_record', 'Previous Record'),
        ('other', 'Other'),
    ]
    UPLOADED_BY_CHOICES = [
        ('patient', 'Patient'),
        ('provider', 'Provider'),
    ]

    session = models.ForeignKey(
        ProviderTelemedicineSession,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file_name = models.CharField(max_length=500)
    file_url = models.URLField()
    file_type = models.CharField(max_length=50)
    file_size_bytes = models.PositiveIntegerField()
    uploaded_by = models.CharField(max_length=20, choices=UPLOADED_BY_CHOICES)
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'cymed_prov_tele_documents'

    def __str__(self):
        return f"{self.file_name} ({self.document_type}) for session {self.session_id}"
