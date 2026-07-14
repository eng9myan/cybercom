from django.db import models

from platform.common.models import BaseModel


class DocumentationTemplate(BaseModel):
    TEMPLATE_TYPE_CHOICES = [
        ("soap", "SOAP"),
        ("progress", "Progress"),
        ("consult", "Consult"),
        ("procedure", "Procedure"),
        ("discharge", "Discharge"),
        ("nursing", "Nursing"),
        ("operative", "Operative"),
        ("transfer", "Transfer"),
        ("referral", "Referral"),
        ("custom", "Custom"),
    ]

    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    specialty = models.CharField(max_length=100, blank=True)
    content_template = models.TextField()
    smart_phrases = models.JSONField(default=list)
    created_by_provider_id = models.UUIDField()
    is_shared = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    version = models.CharField(max_length=20, default="1.0")

    class Meta:
        db_table = "cymed_prov_doc_templates"

    def __str__(self):
        return f"{self.name} ({self.template_type})"


class SmartPhrase(BaseModel):
    PHRASE_TYPE_CHOICES = [
        ("phrase", "Phrase"),
        ("abbreviation", "Abbreviation"),
        ("template_block", "Template Block"),
    ]

    code = models.CharField(max_length=100)
    expansion = models.TextField()
    phrase_type = models.CharField(max_length=20, choices=PHRASE_TYPE_CHOICES, default="phrase")
    created_by_provider_id = models.UUIDField()
    is_personal = models.BooleanField(default=True)
    specialty = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_prov_smart_phrases"
        unique_together = [("tenant_id", "created_by_provider_id", "code")]

    def __str__(self):
        return f"{self.code} -> {self.expansion[:50]}"


class ProviderClinicalNote(BaseModel):
    NOTE_TYPE_CHOICES = [
        ("soap", "SOAP"),
        ("progress", "Progress"),
        ("consult", "Consult"),
        ("procedure", "Procedure"),
        ("discharge", "Discharge"),
        ("nursing", "Nursing"),
        ("addendum", "Addendum"),
        ("operative", "Operative"),
        ("transfer", "Transfer"),
        ("referral", "Referral"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_review", "In Review"),
        ("signed", "Signed"),
        ("amended", "Amended"),
        ("cancelled", "Cancelled"),
    ]

    patient_id = models.UUIDField(db_index=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    author_provider_id = models.UUIDField(db_index=True)
    author_name = models.CharField(max_length=255)
    author_type = models.CharField(max_length=100)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES)
    note_title = models.CharField(max_length=500, blank=True)
    note_body = models.TextField()
    template_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.UUIDField(null=True, blank=True)
    amended_at = models.DateTimeField(null=True, blank=True)
    amendment_reason = models.TextField(blank=True)
    cymed_document_id = models.UUIDField(null=True, blank=True)
    fhir_composition_id = models.CharField(max_length=255, blank=True)
    is_confidential = models.BooleanField(default=False)
    ai_summary = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_prov_clinical_notes"
        indexes = [
            models.Index(fields=["tenant_id", "patient_id", "note_type"]),
            models.Index(fields=["tenant_id", "author_provider_id", "status"]),
        ]

    def __str__(self):
        return f"{self.note_type} note by {self.author_name} for patient {self.patient_id}"


class NoteCoSignature(BaseModel):
    ROLE_CHOICES = [
        ("supervisor", "Supervisor"),
        ("attending", "Attending"),
        ("cosigner", "Cosigner"),
    ]

    note = models.ForeignKey(
        ProviderClinicalNote,
        on_delete=models.CASCADE,
        related_name="cosignatures",
    )
    cosigner_provider_id = models.UUIDField()
    cosigner_name = models.CharField(max_length=255)
    cosigner_type = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    requested_at = models.DateTimeField(auto_now_add=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_prov_note_cosignatures"

    def __str__(self):
        return f"CoSignature by {self.cosigner_name} for note {self.note_id}"


class VoiceDictation(BaseModel):
    STATUS_CHOICES = [
        ("recording", "Recording"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    note = models.ForeignKey(
        ProviderClinicalNote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dictations",
    )
    provider_id = models.UUIDField()
    audio_url = models.URLField(blank=True)
    transcript_text = models.TextField(blank=True)
    ai_transcript = models.TextField(blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="recording")
    integration_provider = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_prov_voice_dictations"

    def __str__(self):
        return f"Dictation by {self.provider_id} ({self.status})"
