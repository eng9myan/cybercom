"""Service functions for the CyMed MRFF Ambient Scribe sub-app."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from .models import ClinicianEdit, ScribeSession, Summary, Transcript


@transaction.atomic
def open_session(
    *,
    tenant_id: UUID | str,
    clinician_profile_id: UUID | str,
    patient_profile_id: UUID | str | None = None,
    encounter_id: UUID | str | None = None,
    consent_kind: str = "verbal_recorded",
    language: str = "en",
    device_platform: str = "",
) -> ScribeSession:
    consent_captured_at = None
    if consent_kind != ScribeSession.ConsentKind.OPTED_OUT:
        consent_captured_at = timezone.now()
    session = ScribeSession.objects.create(
        tenant_id=tenant_id,
        clinician_profile_id=clinician_profile_id,
        patient_profile_id=patient_profile_id,
        encounter_id=encounter_id,
        consent_kind=consent_kind,
        consent_captured_at=consent_captured_at,
        language=language,
        device_platform=device_platform,
        status=ScribeSession.Status.RECORDING,
    )
    return session


@transaction.atomic
def upload_audio(
    *,
    session_id: UUID | str,
    audio_url: str,
    duration_seconds: int,
    stt_model: str = "whisper-large-v3",
) -> ScribeSession:
    session = ScribeSession.objects.select_for_update().get(pk=session_id)
    session.audio_url = audio_url
    session.duration_seconds = duration_seconds
    session.stt_model = stt_model
    session.status = ScribeSession.Status.UPLOADED
    session.ended_at = timezone.now()
    session.save(
        update_fields=[
            "audio_url",
            "duration_seconds",
            "stt_model",
            "status",
            "ended_at",
            "updated_at",
        ]
        if _has_updated_at(session)
        else ["audio_url", "duration_seconds", "stt_model", "status", "ended_at"]
    )
    return session


@transaction.atomic
def transcribe(*, session_id: UUID | str) -> Transcript:
    session = ScribeSession.objects.select_for_update().get(pk=session_id)
    session.status = ScribeSession.Status.TRANSCRIBING
    session.save(
        update_fields=["status", "updated_at"]
        if _has_updated_at(session)
        else ["status"]
    )
    transcript = Transcript.objects.create(
        session=session,
        provider=Transcript.Provider.WHISPER,
        text="[stub]",
        segments=[],
        language=session.language,
    )
    session.status = ScribeSession.Status.TRANSCRIBED
    session.save(
        update_fields=["status", "updated_at"]
        if _has_updated_at(session)
        else ["status"]
    )
    return transcript


@transaction.atomic
def summarise(
    *,
    session_id: UUID | str,
    provider: str = "cygpt",
    summary_model: str = "cygpt-clinical-v1",
) -> Summary:
    session = ScribeSession.objects.select_for_update().get(pk=session_id)
    session.status = ScribeSession.Status.SUMMARISING
    session.summary_model = summary_model
    session.save(
        update_fields=["status", "summary_model", "updated_at"]
        if _has_updated_at(session)
        else ["status", "summary_model"]
    )
    latest_version = (
        Summary.objects.filter(session=session)
        .order_by("-version")
        .values_list("version", flat=True)
        .first()
    )
    next_version = (latest_version or 0) + 1
    summary = Summary.objects.create(
        session=session,
        provider=provider,
        version=next_version,
        soap={
            "subjective": "[stub]",
            "objective": "[stub]",
            "assessment": "[stub]",
            "plan": "[stub]",
        },
        structured={},
        icd_suggestions=[],
        cpt_suggestions=[],
        differentials=[],
    )
    session.status = ScribeSession.Status.DRAFTED
    session.save(
        update_fields=["status", "updated_at"]
        if _has_updated_at(session)
        else ["status"]
    )
    return summary


@transaction.atomic
def clinician_edit(
    *,
    summary_id: UUID | str,
    clinician_profile_id: UUID | str,
    diff: dict[str, Any],
    final_note: str,
    signed: bool = False,
) -> ClinicianEdit:
    summary = Summary.objects.select_related("session").get(pk=summary_id)
    signed_at = timezone.now() if signed else None
    edit = ClinicianEdit.objects.create(
        summary=summary,
        clinician_profile_id=clinician_profile_id,
        diff=diff or {},
        final_note=final_note or "",
        signed=signed,
        signed_at=signed_at,
    )
    if signed:
        session = summary.session
        session.status = ScribeSession.Status.SIGNED
        session.save(
            update_fields=["status", "updated_at"]
            if _has_updated_at(session)
            else ["status"]
        )
    return edit


@transaction.atomic
def discard_session(*, session_id: UUID | str, reason: str) -> ScribeSession:
    session = ScribeSession.objects.select_for_update().get(pk=session_id)
    session.status = ScribeSession.Status.DISCARDED
    session.ended_at = session.ended_at or timezone.now()
    session.save(
        update_fields=["status", "ended_at", "updated_at"]
        if _has_updated_at(session)
        else ["status", "ended_at"]
    )
    return session


def _has_updated_at(instance: Any) -> bool:
    return any(f.name == "updated_at" for f in instance._meta.get_fields())
