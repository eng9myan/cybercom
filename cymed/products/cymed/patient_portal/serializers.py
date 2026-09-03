from rest_framework import serializers

from .models import (
    ConsentGrant,
    DelegatedAccess,
    EmergencyProfile,
    NFCCard,
    NFCScanLog,
    PatientDevice,
    PatientPortalActivity,
    PatientPortalNotificationPreference,
    PatientPortalProfile,
)


class PatientPortalProfileSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.__str__", read_only=True)
    mrn = serializers.CharField(source="patient.mrn", read_only=True)

    class Meta:
        model = PatientPortalProfile
        fields = [
            "id", "patient", "patient_name", "mrn", "user_id",
            "email_verified", "phone_verified", "two_factor_enabled",
            "preferred_language", "theme_preference",
            "nfc_card_id", "nfc_card_activated",
            "emergency_access_enabled", "data_sharing_consent",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user_id", "created_at", "updated_at", "mrn", "patient_name"]


class PatientPortalActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientPortalActivity
        fields = ["id", "activity_type", "description", "ip_address", "created_at"]


class PatientPortalNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientPortalNotificationPreference
        fields = [
            "id", "channel",
            "appointment_reminders", "lab_results_ready",
            "prescription_ready", "billing_updates", "health_tips",
        ]


class PatientDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDevice
        fields = ["id", "platform", "device_id", "device_name",
                  "last_seen_at", "revoked", "created_at"]
        read_only_fields = ["id", "last_seen_at", "created_at"]


class NFCCardSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = NFCCard
        fields = ["id", "card_uuid", "chip_vendor",
                  "issued_at", "activated_at", "revoked_at",
                  "revocation_reason", "is_active"]
        read_only_fields = fields


class NFCCardCreateSerializer(serializers.Serializer):
    profile_id = serializers.UUIDField()
    public_key_pem = serializers.CharField()
    chip_vendor = serializers.ChoiceField(
        choices=["desfire_ev3", "ntag424"], default="desfire_ev3"
    )


class NFCScanLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFCScanLog
        fields = ["id", "card", "profile", "scanned_at", "purpose",
                  "provider_tenant_id", "provider_name", "terminal_id",
                  "scope_granted", "patient_notified_at"]
        read_only_fields = fields


class NFCScanPublicRequestSerializer(serializers.Serializer):
    card_uuid = serializers.UUIDField()
    signature = serializers.CharField()
    nonce = serializers.CharField()
    purpose = serializers.ChoiceField(
        choices=["reception", "pharmacy", "lab", "imaging", "emergency", "other"]
    )
    terminal_id = serializers.CharField(max_length=200)


class EmergencyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyProfile
        fields = ["id", "blood_type", "allergies", "current_medications",
                  "chronic_conditions", "emergency_contacts",
                  "dnr_status", "organ_donor", "religious_preferences",
                  "preferred_language", "updated_from_ehr_at", "updated_at"]
        read_only_fields = ["id", "updated_from_ehr_at", "updated_at"]


class DelegatedAccessSerializer(serializers.ModelSerializer):
    subject_mrn = serializers.CharField(source="subject_profile.patient.mrn", read_only=True)
    delegate_mrn = serializers.CharField(source="delegate_profile.patient.mrn", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = DelegatedAccess
        fields = ["id", "subject_profile", "delegate_profile",
                  "subject_mrn", "delegate_mrn", "relationship",
                  "scope_read_records", "scope_book_appt",
                  "scope_pay_bills", "scope_max_amount", "scope_expiry",
                  "accepted_at", "consent_signed_at", "revoked_at",
                  "is_active", "created_at"]
        read_only_fields = ["id", "accepted_at", "consent_signed_at",
                            "revoked_at", "is_active", "created_at",
                            "subject_mrn", "delegate_mrn"]


class ConsentGrantSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = ConsentGrant
        fields = ["id", "profile", "provider_tenant_id", "scope",
                  "purpose", "valid_from", "valid_until", "revoked_at",
                  "is_active", "created_at"]
        read_only_fields = ["id", "revoked_at", "is_active", "created_at"]
