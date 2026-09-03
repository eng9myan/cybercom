"""URL routes for the CyMed MRFF Ambient Scribe sub-app."""

from django.urls import path

from .views import (
    ClinicianEditViewSet,
    ScribeSessionViewSet,
    SummaryViewSet,
    TranscriptViewSet,
)

urlpatterns = [
    path(
        "sessions/",
        ScribeSessionViewSet.as_view({"get": "list", "post": "create"}),
        name="ambient-scribe-session-list",
    ),
    path(
        "sessions/open/",
        ScribeSessionViewSet.as_view({"post": "open"}),
        name="ambient-scribe-session-open",
    ),
    path(
        "sessions/<uuid:pk>/",
        ScribeSessionViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="ambient-scribe-session-detail",
    ),
    path(
        "sessions/<uuid:pk>/upload-audio/",
        ScribeSessionViewSet.as_view({"post": "upload_audio"}),
        name="ambient-scribe-session-upload-audio",
    ),
    path(
        "sessions/<uuid:pk>/transcribe/",
        ScribeSessionViewSet.as_view({"post": "transcribe"}),
        name="ambient-scribe-session-transcribe",
    ),
    path(
        "sessions/<uuid:pk>/summarise/",
        ScribeSessionViewSet.as_view({"post": "summarise"}),
        name="ambient-scribe-session-summarise",
    ),
    path(
        "sessions/<uuid:pk>/discard/",
        ScribeSessionViewSet.as_view({"post": "discard"}),
        name="ambient-scribe-session-discard",
    ),
    path(
        "transcripts/",
        TranscriptViewSet.as_view({"get": "list"}),
        name="ambient-scribe-transcript-list",
    ),
    path(
        "transcripts/<uuid:pk>/",
        TranscriptViewSet.as_view({"get": "retrieve"}),
        name="ambient-scribe-transcript-detail",
    ),
    path(
        "summaries/",
        SummaryViewSet.as_view({"get": "list"}),
        name="ambient-scribe-summary-list",
    ),
    path(
        "summaries/<uuid:pk>/",
        SummaryViewSet.as_view({"get": "retrieve"}),
        name="ambient-scribe-summary-detail",
    ),
    path(
        "edits/",
        ClinicianEditViewSet.as_view({"get": "list", "post": "create"}),
        name="ambient-scribe-edit-list",
    ),
    path(
        "edits/apply/",
        ClinicianEditViewSet.as_view({"post": "apply"}),
        name="ambient-scribe-edit-apply",
    ),
    path(
        "edits/<uuid:pk>/",
        ClinicianEditViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="ambient-scribe-edit-detail",
    ),
]
