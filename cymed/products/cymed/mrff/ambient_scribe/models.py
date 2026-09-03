"""Domain models for the CyMed MRFF Ambient Scribe sub-app."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class ScribeSession(BaseModel):
    class ConsentKind(models.TextChoices):
        VERBAL_RECORDED = "verbal_recorded", "Verbal Recorded"
        WRITTEN = "written", "Written"
        OPTED_OUT = "opted_out", "Opted Out"

    class Status(models.TextChoices):
        RECORDING = "recording", "Recording"
        UPLOADED = "uploaded", "Uploaded"
        TRANSCRIBING = "transcribing", "Transcribing"
        TRANSCRIBED = "transcribed", "Transcribed"
        SUMMARISING = "summarising", "Summarising"
        DRAFTED = "drafted", "Drafted"
        SIGNED = "signed", "Signed"
        DISCARDED = "discarded", "Discarded"
        FAILED = "failed", "Failed"

    tenant_id = models.UUIDField(db_index=True)
    clinician_profile_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(null=True, blank=True, db_index=True)
    encounter_id = models.UUIDField(null=True, blank=True)
    consent_kind = models.CharField(
        max_length=32,
        choices=ConsentKind.choices,
        default=ConsentKind.VERBAL_RECORDED,
    )
    consent_captured_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    language = models.CharField(max_length=8, default="en")
    device_platform = models.CharField(max_length=32, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.RECORDING,
    )
    audio_url = models.URLField(blank=True)
    duration_seconds = models.IntegerField(default=0)
    stt_model = models.CharField(max_length=64, blank=True)
    summary_model = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "cymed_mrff_ambient_scribe_scribe_session"

    def __str__(self) -> str:
        return f"ScribeSession({self.pk})"


class Transcript(BaseModel):
    class Provider(models.TextChoices):
        WHISPER = "whisper", "Whisper"
        AZURE_STT = "azure_stt", "Azure STT"
        AWS_TRANSCRIBE = "aws_transcribe", "AWS Transcribe"
        VOSK_OFFLINE = "vosk_offline", "Vosk Offline"
        VENDOR_CUSTOM = "vendor_custom", "Vendor Custom"

    session = models.ForeignKey(
        ScribeSession,
        on_delete=models.CASCADE,
        related_name="transcripts",
    )
    provider = models.CharField(
        max_length=32,
        choices=Provider.choices,
        default=Provider.WHISPER,
    )
    text = models.TextField(blank=True)
    segments = models.JSONField(default=list, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0"))
    language = models.CharField(max_length=8, default="en")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_mrff_ambient_scribe_transcript"

    def __str__(self) -> str:
        return f"Transcript({self.pk})"


class Summary(BaseModel):
    class Provider(models.TextChoices):
        CYGPT = "cygpt", "CyGPT"
        AZURE_OPENAI = "azure_openai", "Azure OpenAI"
        BEDROCK_CLAUDE = "bedrock_claude", "Bedrock Claude"
        VERTEX_GEMINI = "vertex_gemini", "Vertex Gemini"
        ON_PREM_LLAMA = "on_prem_llama", "On-Prem Llama"

    session = models.ForeignKey(
        ScribeSession,
        on_delete=models.CASCADE,
        related_name="summaries",
    )
    provider = models.CharField(
        max_length=32,
        choices=Provider.choices,
        default=Provider.CYGPT,
    )
    version = models.IntegerField(default=1)
    soap = models.JSONField(default=dict, blank=True)
    structured = models.JSONField(default=dict, blank=True)
    icd_suggestions = models.JSONField(default=list, blank=True)
    cpt_suggestions = models.JSONField(default=list, blank=True)
    differentials = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField(default=timezone.now)
    prompt_token_count = models.IntegerField(default=0)
    output_token_count = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=9, decimal_places=4, default=Decimal("0"))

    class Meta:
        db_table = "cymed_mrff_ambient_scribe_summary"

    def __str__(self) -> str:
        return f"Summary({self.pk})"


class ClinicianEdit(BaseModel):
    summary = models.ForeignKey(
        Summary,
        on_delete=models.CASCADE,
        related_name="edits",
    )
    clinician_profile_id = models.UUIDField(db_index=True)
    edited_at = models.DateTimeField(default=timezone.now)
    diff = models.JSONField(default=dict, blank=True)
    final_note = models.TextField(blank=True)
    signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_mrff_ambient_scribe_clinician_edit"

    def __str__(self) -> str:
        return f"ClinicianEdit({self.pk})"
