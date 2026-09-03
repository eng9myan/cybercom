from rest_framework import serializers

from .models import AppealCase, Claim837, ClaimResponse, DenialCode


class Claim837Serializer(serializers.ModelSerializer):
    class Meta:
        model = Claim837
        fields = ["id", "claim_number", "bill_id", "encounter_id",
                  "patient_profile_id", "kind", "payer_code", "payer_country",
                  "diagnosis_codes", "procedure_codes", "charge_total",
                  "status", "scrub_errors", "denial_risk", "denial_risk_drivers",
                  "external_reference", "submitted_at", "accepted_at",
                  "paid_at", "denied_at", "dso_days", "created_at"]
        read_only_fields = ["id", "claim_number", "scrub_errors",
                              "denial_risk", "denial_risk_drivers",
                              "external_reference", "submitted_at",
                              "accepted_at", "paid_at", "denied_at",
                              "dso_days", "created_at"]


class ClaimResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimResponse
        fields = "__all__"


class AppealCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppealCase
        fields = "__all__"
        read_only_fields = ["id", "appeal_letter_html", "submitted_at",
                              "decided_at", "recovered_amount", "created_at"]


class DenialCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DenialCode
        fields = "__all__"
