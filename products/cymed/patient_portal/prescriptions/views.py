from rest_framework import filters, permissions, viewsets

from .models import (
    MedicationAdherenceLog,
    MedicationInstruction,
    PortalPrescriptionView,
    RefillRequest,
)
from .serializers import (
    MedicationAdherenceLogSerializer,
    MedicationInstructionSerializer,
    PortalPrescriptionViewSerializer,
    RefillRequestSerializer,
)


class PortalPrescriptionViewViewSet(viewsets.ModelViewSet):
    serializer_class = PortalPrescriptionViewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "prescription_number",
        "prescriber_name",
        "pharmacy_name",
        "prescription_type",
    ]
    ordering_fields = ["prescribed_at", "valid_until", "status", "created_at"]
    ordering = ["-prescribed_at"]

    def get_queryset(self):
        qs = PortalPrescriptionView.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        status = self.request.query_params.get("status")
        is_controlled = self.request.query_params.get("is_controlled")
        can_request_refill = self.request.query_params.get("can_request_refill")
        is_viewed = self.request.query_params.get("is_viewed")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if status:
            qs = qs.filter(status=status)
        if is_controlled is not None:
            qs = qs.filter(is_controlled=is_controlled.lower() == "true")
        if can_request_refill is not None:
            qs = qs.filter(can_request_refill=can_request_refill.lower() == "true")
        if is_viewed is not None:
            qs = qs.filter(is_viewed=is_viewed.lower() == "true")
        return qs


class RefillRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RefillRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["submitted_at", "status", "estimated_ready_at"]
    ordering = ["-submitted_at"]

    def get_queryset(self):
        qs = RefillRequest.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        status = self.request.query_params.get("status")
        portal_prescription_id = self.request.query_params.get("portal_prescription_id")
        pickup_method = self.request.query_params.get("pickup_method")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if status:
            qs = qs.filter(status=status)
        if portal_prescription_id:
            qs = qs.filter(portal_prescription_id=portal_prescription_id)
        if pickup_method:
            qs = qs.filter(pickup_method=pickup_method)
        return qs


class MedicationInstructionViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationInstructionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["drug_name", "drug_code", "instruction_text"]
    ordering_fields = ["drug_name", "drug_code", "created_at"]
    ordering = ["drug_name"]

    def get_queryset(self):
        qs = MedicationInstruction.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        drug_code = self.request.query_params.get("drug_code")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if drug_code:
            qs = qs.filter(drug_code=drug_code)
        return qs


class MedicationAdherenceLogViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationAdherenceLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["drug_name", "drug_code"]
    ordering_fields = ["scheduled_time", "taken_at", "status", "created_at"]
    ordering = ["-scheduled_time"]

    def get_queryset(self):
        qs = MedicationAdherenceLog.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        status = self.request.query_params.get("status")
        portal_prescription_id = self.request.query_params.get("portal_prescription_id")
        drug_code = self.request.query_params.get("drug_code")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if status:
            qs = qs.filter(status=status)
        if portal_prescription_id:
            qs = qs.filter(portal_prescription_id=portal_prescription_id)
        if drug_code:
            qs = qs.filter(drug_code=drug_code)
        return qs
