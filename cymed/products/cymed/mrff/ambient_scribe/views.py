"""DRF viewsets for the CyMed MRFF Ambient Scribe sub-app."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import ClinicianEdit, ScribeSession, Summary, Transcript
from .serializers import (
    ClinicianEditSerializer,
    ScribeSessionSerializer,
    SummarySerializer,
    TranscriptSerializer,
)


class ScribeSessionViewSet(viewsets.ModelViewSet):
    queryset = ScribeSession.objects.all()
    serializer_class = ScribeSessionSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open(self, request):
        session = services.open_session(
            tenant_id=request.data.get("tenant_id"),
            clinician_profile_id=request.data.get("clinician_profile_id"),
            patient_profile_id=request.data.get("patient_profile_id"),
            encounter_id=request.data.get("encounter_id"),
            consent_kind=request.data.get("consent_kind", "verbal_recorded"),
            language=request.data.get("language", "en"),
            device_platform=request.data.get("device_platform", ""),
        )
        return Response(ScribeSessionSerializer(session).data)

    @action(detail=True, methods=["post"], url_path="upload-audio")
    def upload_audio(self, request, pk=None):
        session = services.upload_audio(
            session_id=pk,
            audio_url=request.data.get("audio_url", ""),
            duration_seconds=int(request.data.get("duration_seconds", 0)),
            stt_model=request.data.get("stt_model", "whisper-large-v3"),
        )
        return Response(ScribeSessionSerializer(session).data)

    @action(detail=True, methods=["post"], url_path="transcribe")
    def transcribe(self, request, pk=None):
        transcript = services.transcribe(session_id=pk)
        return Response(TranscriptSerializer(transcript).data)

    @action(detail=True, methods=["post"], url_path="summarise")
    def summarise(self, request, pk=None):
        summary = services.summarise(
            session_id=pk,
            provider=request.data.get("provider", "cygpt"),
            summary_model=request.data.get("summary_model", "cygpt-clinical-v1"),
        )
        return Response(SummarySerializer(summary).data)

    @action(detail=True, methods=["post"], url_path="discard")
    def discard(self, request, pk=None):
        session = services.discard_session(
            session_id=pk,
            reason=request.data.get("reason", ""),
        )
        return Response(ScribeSessionSerializer(session).data)


class TranscriptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transcript.objects.all()
    serializer_class = TranscriptSerializer


class SummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Summary.objects.all()
    serializer_class = SummarySerializer


class ClinicianEditViewSet(viewsets.ModelViewSet):
    queryset = ClinicianEdit.objects.all()
    serializer_class = ClinicianEditSerializer

    @action(detail=False, methods=["post"], url_path="apply")
    def apply(self, request):
        edit = services.clinician_edit(
            summary_id=request.data.get("summary_id"),
            clinician_profile_id=request.data.get("clinician_profile_id"),
            diff=request.data.get("diff", {}),
            final_note=request.data.get("final_note", ""),
            signed=bool(request.data.get("signed", False)),
        )
        return Response(ClinicianEditSerializer(edit).data)
