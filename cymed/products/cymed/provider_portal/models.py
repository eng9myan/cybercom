from django.db import models

from platform.common.models import BaseModel


class ProviderPortalProfile(BaseModel):
    """Provider portal user profile linked to a Provider record."""

    provider = models.OneToOneField(
        "cymed_providers.Provider",
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
    dashboard_layout = models.JSONField(default=dict, blank=True)
    quick_actions = models.JSONField(default=list, blank=True)
    is_on_call = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_provider_portal_profiles"

    def __str__(self):
        return f"ProviderPortal({self.provider.npi})"


class ProviderPortalActivity(BaseModel):
    """Audit trail of provider portal activities."""

    ACTIVITY_TYPES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("patient_viewed", "Patient Viewed"),
        ("prescription_issued", "Prescription Issued"),
        ("lab_ordered", "Lab Ordered"),
        ("imaging_ordered", "Imaging Ordered"),
        ("referral_sent", "Referral Sent"),
        ("note_added", "Clinical Note Added"),
        ("schedule_updated", "Schedule Updated"),
    ]

    profile = models.ForeignKey(
        ProviderPortalProfile, on_delete=models.CASCADE, related_name="activities"
    )
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    patient_mrn = models.CharField(max_length=100, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_provider_portal_activities"
        ordering = ["-created_at"]


class ProviderCredentialingStatus(BaseModel):
    """Tracks provider credentialing and verification status."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("verified", "Verified"),
        ("expired", "Expired"),
        ("suspended", "Suspended"),
    ]

    provider = models.OneToOneField(
        "cymed_providers.Provider",
        on_delete=models.CASCADE,
        related_name="credentialing_status",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    verified_by = models.CharField(max_length=255, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    license_verified = models.BooleanField(default=False)
    board_certification_verified = models.BooleanField(default=False)
    background_check_passed = models.BooleanField(default=False)
    malpractice_insurance_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_provider_credentialing_status"

    def __str__(self):
        return f"Credentialing({self.provider.npi}, {self.status})"
