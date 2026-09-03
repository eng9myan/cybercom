"""ViewSets exposing prep instruction templates, assignments, checklist items, and consent."""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import ContrastConsent, PrepAssignment, PrepChecklistItem, PrepTemplate
from .serializers import (
    ContrastConsentSerializer,
    PrepAssignmentSerializer,
    PrepChecklistItemSerializer,
    PrepTemplateSerializer,
)


class PrepTemplateViewSet(viewsets.ModelViewSet):
    queryset = PrepTemplate.objects.all()
    serializer_class = PrepTemplateSerializer

    @action(detail=False, methods=["post"], url_path="create-template")
    def create_template(self, request):
        data = request.data
        obj = services.create_template(
            code=data.get("code"),
            title=data.get("title"),
            title_ar=data.get("title_ar", ""),
            modality=data.get("modality"),
            body_part=data.get("body_part", ""),
            contrast_involved=data.get("contrast_involved", False),
            fasting_required=data.get("fasting_required", False),
            fasting_hours=data.get("fasting_hours", 0),
            hydration_required=data.get("hydration_required", False),
            medications_to_hold=data.get("medications_to_hold"),
            clothing_instructions=data.get("clothing_instructions", ""),
            arrive_minutes_before=data.get("arrive_minutes_before", 15),
            what_to_bring=data.get("what_to_bring"),
            body_html=data.get("body_html", ""),
            body_html_ar=data.get("body_html_ar", ""),
            tenant_id=data.get("tenant_id"),
            version=data.get("version", 1),
        )
        return Response(PrepTemplateSerializer(obj).data)


class PrepAssignmentViewSet(viewsets.ModelViewSet):
    queryset = PrepAssignment.objects.all()
    serializer_class = PrepAssignmentSerializer

    @action(detail=False, methods=["post"], url_path="assign")
    def assign(self, request):
        data = request.data
        obj = services.assign_prep(
            tenant_id=data.get("tenant_id"),
            patient_profile_id=data.get("patient_profile_id"),
            template_id=data.get("template_id"),
            booking_id=data.get("booking_id"),
            language=data.get("language", "en"),
        )
        return Response(PrepAssignmentSerializer(obj).data)

    @action(detail=True, methods=["post"], url_path="record-view")
    def record_view(self, request, pk=None):
        obj = services.record_view(assignment_id=pk)
        return Response(PrepAssignmentSerializer(obj).data)

    @action(detail=True, methods=["post"], url_path="mark-item")
    def mark_item(self, request, pk=None):
        data = request.data
        obj = services.mark_item(
            assignment_id=pk,
            item_id=data.get("item_id"),
            checked=bool(data.get("checked", False)),
            note=data.get("note", ""),
        )
        return Response(PrepChecklistItemSerializer(obj).data)


class PrepChecklistItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PrepChecklistItem.objects.all()
    serializer_class = PrepChecklistItemSerializer


class ContrastConsentViewSet(viewsets.ModelViewSet):
    queryset = ContrastConsent.objects.all()
    serializer_class = ContrastConsentSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open_consent(self, request):
        data = request.data
        obj = services.open_contrast_consent(
            tenant_id=data.get("tenant_id"),
            patient_profile_id=data.get("patient_profile_id"),
            contrast_kind=data.get("contrast_kind"),
            assignment_id=data.get("assignment_id"),
        )
        return Response(ContrastConsentSerializer(obj).data)

    @action(detail=True, methods=["post"], url_path="sign")
    def sign(self, request, pk=None):
        data = request.data
        obj = services.sign_contrast_consent(
            consent_id=pk,
            signature_url=data.get("signature_url"),
            witness_profile_id=data.get("witness_profile_id"),
            allergies_reviewed=data.get("allergies_reviewed", True),
            egfr_verified=data.get("egfr_verified", False),
            egfr_value=data.get("egfr_value"),
            pregnancy_status=data.get("pregnancy_status", "unknown"),
        )
        return Response(ContrastConsentSerializer(obj).data)

    @action(detail=True, methods=["post"], url_path="decline")
    def decline(self, request, pk=None):
        data = request.data
        obj = services.decline_contrast(
            consent_id=pk,
            reason=data.get("reason", ""),
        )
        return Response(ContrastConsentSerializer(obj).data)
