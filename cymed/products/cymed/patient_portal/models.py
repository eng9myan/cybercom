"""
Patient Portal models — expanded per P0-1 spec.

Adds:
  PatientDevice        registered mobile/web devices with WebAuthn credentials
  NFCCard              physical NFC card issued to patient
  NFCScanLog           audit of every scan (patient-visible)
  EmergencyProfile     paramedic-scan snapshot
  DelegatedAccess      family / caregiver grants
  ConsentGrant         fine-grained provider consents
"""
import uuid

from django.db import models

from platform.common.models import BaseModel, SoftDeleteMixin


# ── existing (kept intact) ──────────────────────────────────────────────
class PatientPortalProfile(BaseModel):
    """Patient portal user profile linked to a Patient record."""

    patient = models.OneToOneField(
        "cymed_patients.Patient",
        on_delete=models.CASCADE,
        related_name="portal_profile",
    )
    user_id = models.UUIDField(db_index=True, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=10, default="en")
    theme_preference = models.CharField(
        max_length=20,
        choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
        default="system",
    )
    nfc_card_id = models.CharField(max_length=255, blank=True, db_index=True)
    nfc_card_activated = models.BooleanField(default=False)
    emergency_access_enabled = models.BooleanField(default=True)
    data_sharing_consent = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_patient_portal_profiles"

    def __str__(self):
        return f"PortalProfile({self.patient.mrn})"


class PatientPortalActivity(BaseModel):
    """Audit trail of patient portal activities."""

    ACTIVITY_TYPES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("appointment_booked", "Appointment Booked"),
        ("appointment_cancelled", "Appointment Cancelled"),
        ("prescription_viewed", "Prescription Viewed"),
        ("lab_result_viewed", "Lab Result Viewed"),
        ("imaging_viewed", "Imaging Viewed"),
        ("profile_updated", "Profile Updated"),
        ("consent_changed", "Consent Changed"),
        ("emergency_access", "Emergency Access Used"),
        ("nfc_scan", "NFC Card Scanned"),
        ("delegated_grant", "Delegation Granted"),
        ("delegated_revoke", "Delegation Revoked"),
    ]

    profile = models.ForeignKey(
        PatientPortalProfile, on_delete=models.CASCADE, related_name="activities"
    )
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_patient_portal_activities"
        ordering = ["-created_at"]


class PatientPortalNotificationPreference(BaseModel):
    """Notification preferences per channel."""

    CHANNELS = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push Notification"),
        ("whatsapp", "WhatsApp"),
    ]

    profile = models.ForeignKey(
        PatientPortalProfile, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    channel = models.CharField(max_length=20, choices=CHANNELS)
    appointment_reminders = models.BooleanField(default=True)
    lab_results_ready = models.BooleanField(default=True)
    prescription_ready = models.BooleanField(default=True)
    billing_updates = models.BooleanField(default=True)
    health_tips = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_patient_portal_notification_preferences"
        unique_together = [("profile", "channel")]


# ── NEW per P0-1 spec ─────────────────────────────────────────────────

class PatientDevice(BaseModel, SoftDeleteMixin):
    """Registered mobile or web device for a patient."""

    PLATFORMS = [("ios", "iOS"), ("android", "Android"), ("web", "Web")]

    profile = models.ForeignKey(
        PatientPortalProfile, on_delete=models.CASCADE, related_name="devices"
    )
    platform = models.CharField(max_length=10, choices=PLATFORMS)
    device_id = models.CharField(max_length=255, db_index=True)
    device_name = models.CharField(max_length=200, blank=True)
    push_token = models.CharField(max_length=500, blank=True)
    webauthn_credential_id = models.CharField(max_length=500, blank=True, db_index=True)
    webauthn_public_key = models.TextField(blank=True)
    webauthn_sign_count = models.BigIntegerField(default=0)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "cymed_patient_devices"
        unique_together = [("profile", "device_id")]
        indexes = [models.Index(fields=["profile", "revoked"])]

    def __str__(self):
        return f"{self.platform}/{self.device_name or self.device_id[:8]}"


class NFCCard(BaseModel, SoftDeleteMixin):
    """Physical NFC card issued to a patient (or dependent)."""

    profile = models.ForeignKey(
        PatientPortalProfile, on_delete=models.CASCADE, related_name="nfc_cards"
    )
    card_uuid = models.UUIDField(unique=True, db_index=True, default=uuid.uuid4)
    public_key_pem = models.TextField(help_text="ECDSA P-256 public key from the card's secure element")
    chip_vendor = models.CharField(
        max_length=50,
        choices=[("desfire_ev3", "NXP MIFARE DESFire EV3"), ("ntag424", "NXP NTAG424 DNA")],
        default="desfire_ev3",
    )
    activation_code_hash = models.CharField(max_length=128, blank=True)
    issued_by_user_id = models.UUIDField(null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "cymed_nfc_cards"

    @property
    def is_active(self) -> bool:
        return self.activated_at is not None and self.revoked_at is None

    def __str__(self):
        return f"NFCCard({self.card_uuid})"


class NFCScanLog(BaseModel):
    """Immutable audit of every NFC scan, patient-visible."""

    PURPOSES = [
        ("reception", "Reception"),
        ("pharmacy", "Pharmacy"),
        ("lab", "Laboratory"),
        ("imaging", "Imaging"),
        ("emergency", "Emergency"),
        ("other", "Other"),
    ]

    card = models.ForeignKey(NFCCard, on_delete=models.CASCADE, related_name="scan_logs")
    profile = models.ForeignKey(
        PatientPortalProfile, on_delete=models.CASCADE, related_name="scan_logs"
    )
    scanned_at = models.DateTimeField(auto_now_add=True, db_index=True)
    purpose = models.CharField(max_length=20, choices=PURPOSES)
    provider_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    provider_name = models.CharField(max_length=200, blank=True)
    terminal_id = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    scope_granted = models.JSONField(default=dict, blank=True)
    patient_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_nfc_scan_logs"
        ordering = ["-scanned_at"]
        indexes = [
            models.Index(fields=["profile", "-scanned_at"]),
            models.Index(fields=["card", "-scanned_at"]),
        ]


class EmergencyProfile(BaseModel):
    """Snapshot used for paramedic NFC scans. Patient-editable, EHR-sourced fallback."""

    DNR_CHOICES = [
        ("none", "None"),
        ("dnr", "DNR (Do Not Resuscitate)"),
        ("dnr_cc", "DNR / Comfort Care"),
        ("unknown", "Unknown"),
    ]

    profile = models.OneToOneField(
        PatientPortalProfile, on_delete=models.CASCADE, related_name="emergency_profile"
    )
    blood_type = models.CharField(max_length=5, blank=True)
    allergies = models.JSONField(
        default=list,
        blank=True,
        help_text="[{substance, severity, reaction}]",
    )
    current_medications = models.JSONField(
        default=list,
        blank=True,
        help_text="[{drug, dose, frequency}]",
    )
    chronic_conditions = models.JSONField(
        default=list,
        blank=True,
        help_text="[{icd11, label}]",
    )
    emergency_contacts = models.JSONField(
        default=list,
        blank=True,
        help_text="[{name, relation, phone}]",
    )
    dnr_status = models.CharField(max_length=20, choices=DNR_CHOICES, default="unknown")
    organ_donor = models.BooleanField(default=False)
    religious_preferences = models.CharField(max_length=200, blank=True)
    preferred_language = models.CharField(max_length=10, default="ar")
    updated_from_ehr_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_emergency_profiles"


class DelegatedAccess(BaseModel, SoftDeleteMixin):
    """Grant of scoped access from a subject patient to a delegate patient."""

    RELATIONSHIPS = [
        ("spouse", "Spouse"),
        ("parent", "Parent"),
        ("child", "Child"),
        ("sibling", "Sibling"),
        ("guardian", "Guardian"),
        ("friend", "Friend"),
        ("other", "Other"),
    ]

    subject_profile = models.ForeignKey(
        PatientPortalProfile,
        on_delete=models.CASCADE,
        related_name="delegations_granted",
        help_text="Patient whose data is being shared",
    )
    delegate_profile = models.ForeignKey(
        PatientPortalProfile,
        on_delete=models.CASCADE,
        related_name="delegations_received",
        help_text="Patient who gets access",
    )
    relationship = models.CharField(max_length=20, choices=RELATIONSHIPS)
    scope_read_records = models.BooleanField(default=False)
    scope_book_appt = models.BooleanField(default=False)
    scope_pay_bills = models.BooleanField(default=True)
    scope_max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    scope_expiry = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    consent_signed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_delegated_access"
        unique_together = [("subject_profile", "delegate_profile")]

    @property
    def is_active(self) -> bool:
        from django.utils import timezone
        if self.revoked_at:
            return False
        if not self.accepted_at:
            return False
        if self.scope_expiry and self.scope_expiry < timezone.now():
            return False
        return True


class ConsentGrant(BaseModel):
    """Fine-grained consent from patient to a specific provider tenant."""

    PURPOSES = [
        ("treatment", "Treatment"),
        ("payment", "Payment"),
        ("operations", "Operations"),
        ("research", "Research"),
    ]

    profile = models.ForeignKey(
        PatientPortalProfile, on_delete=models.CASCADE, related_name="consents"
    )
    provider_tenant_id = models.UUIDField(db_index=True)
    scope = models.JSONField(
        default=dict,
        help_text='e.g. {"resources": ["Observation", "MedicationRequest"], "categories": ["laboratory"]}',
    )
    purpose = models.CharField(max_length=20, choices=PURPOSES, default="treatment")
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_consent_grants"
        indexes = [
            models.Index(fields=["profile", "provider_tenant_id"]),
            models.Index(fields=["provider_tenant_id", "purpose"]),
        ]

    @property
    def is_active(self) -> bool:
        from django.utils import timezone
        now = timezone.now()
        if self.revoked_at:
            return False
        if self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        return True
