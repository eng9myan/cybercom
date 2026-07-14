from django.db import models

from platform.common.models import BaseModel

ID_TYPE_CHOICES = [
    ("national_id", "National ID"),
    ("resident_id", "Resident ID"),
    ("passport", "Passport"),
    ("gulfid", "Gulf ID"),
    ("other", "Other"),
]

ID_STATUS_CHOICES = [
    ("active", "Active"),
    ("suspended", "Suspended"),
    ("revoked", "Revoked"),
    ("pending_verification", "Pending Verification"),
]

CERTIFICATE_STATUS_CHOICES = [
    ("valid", "Valid"),
    ("expired", "Expired"),
    ("revoked", "Revoked"),
    ("pending", "Pending"),
]

PASS_TYPE_CHOICES = [
    ("travel", "Travel"),
    ("event", "Event"),
    ("workplace", "Workplace"),
    ("education", "Education"),
    ("healthcare_access", "Healthcare Access"),
]

PASS_STATUS_CHOICES = [
    ("active", "Active"),
    ("expired", "Expired"),
    ("revoked", "Revoked"),
    ("suspended", "Suspended"),
]

WALLET_ENTRY_TYPE_CHOICES = [
    ("medical_record", "Medical Record"),
    ("vaccination_certificate", "Vaccination Certificate"),
    ("insurance_card", "Insurance Card"),
    ("prescription", "Prescription"),
    ("lab_result", "Lab Result"),
    ("imaging_report", "Imaging Report"),
    ("allergy_record", "Allergy Record"),
    ("health_pass", "Health Pass"),
    ("other", "Other"),
]


class NationalHealthID(BaseModel):
    class Meta:
        app_label = "cymed_ph_digital_health"
        db_table = "cymed_ph_dh_national_ids"
        unique_together = [["tenant_id", "patient_id"]]

    patient_id = models.UUIDField(db_index=True)
    national_id_number = models.CharField(max_length=100, unique=True)
    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES, default="national_id")
    id_status = models.CharField(
        max_length=20, choices=ID_STATUS_CHOICES, default="pending_verification"
    )
    issued_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    issuing_authority = models.CharField(max_length=200, blank=True)
    verification_date = models.DateField(null=True, blank=True)
    verified_by_user_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.national_id_number} ({self.id_type})"


class VaccinationCertificate(BaseModel):
    class Meta:
        app_label = "cymed_ph_digital_health"
        db_table = "cymed_ph_dh_vaccination_certs"

    patient_id = models.UUIDField(db_index=True)
    vaccine_name = models.CharField(max_length=200)
    # CVX code from TerminologyService — no local term table
    vaccine_code = models.CharField(max_length=50, blank=True)
    dose_number = models.PositiveSmallIntegerField(default=1)
    total_doses = models.PositiveSmallIntegerField(default=1)
    vaccination_date = models.DateField()
    facility_id = models.UUIDField(null=True, blank=True)
    provider_id = models.UUIDField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    certificate_number = models.CharField(max_length=100, unique=True)
    validity_start = models.DateField()
    validity_end = models.DateField(null=True, blank=True)
    # Encoded certificate data for QR generation
    qr_code_data = models.TextField(blank=True)
    certificate_status = models.CharField(
        max_length=20, choices=CERTIFICATE_STATUS_CHOICES, default="valid"
    )
    # IHR compliant international certificate
    is_international = models.BooleanField(default=False)
    fhir_immunization_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.vaccine_name} — {self.certificate_number}"


class HealthPass(BaseModel):
    class Meta:
        app_label = "cymed_ph_digital_health"
        db_table = "cymed_ph_dh_health_passes"

    patient_id = models.UUIDField(db_index=True)
    pass_type = models.CharField(max_length=20, choices=PASS_TYPE_CHOICES)
    pass_name = models.CharField(max_length=200)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    # List of conditions/requirements met for this pass
    conditions_met = models.JSONField(default=list)
    pass_status = models.CharField(max_length=20, choices=PASS_STATUS_CHOICES, default="active")
    qr_code_data = models.TextField(blank=True)
    issued_by_authority = models.CharField(max_length=200, blank=True)
    revocation_reason = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return f"{self.pass_name} ({self.pass_type}) — {self.patient_id}"


class DigitalHealthWalletEntry(BaseModel):
    class Meta:
        app_label = "cymed_ph_digital_health"
        db_table = "cymed_ph_dh_wallet_entries"

    patient_id = models.UUIDField(db_index=True)
    entry_type = models.CharField(max_length=30, choices=WALLET_ENTRY_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # CyData file URL reference
    content_reference = models.CharField(max_length=500, blank=True)
    issue_date = models.DateField()
    validity_date = models.DateField(null=True, blank=True)
    issuing_authority = models.CharField(max_length=200, blank=True)
    issuing_facility_id = models.UUIDField(null=True, blank=True)
    is_shareable = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_source = models.CharField(max_length=200, blank=True)
    qr_code_data = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} ({self.entry_type}) — {self.patient_id}"
