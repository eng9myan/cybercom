import uuid
from django.db import models
from platform.common.models import BaseModel


class HealthWallet(BaseModel):
    account_id = models.UUIDField(unique=True, db_index=True)
    patient_id = models.UUIDField(db_index=True)
    wallet_name = models.CharField(max_length=100, default='My Health Wallet')
    is_active = models.BooleanField(default=True)
    card_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'cymed_portal_health_wallets'

    def __str__(self):
        return f"{self.wallet_name} ({self.account_id})"


class DigitalCard(BaseModel):
    CARD_TYPE_CHOICES = [
        ('patient_id', 'Patient ID'),
        ('insurance', 'Insurance'),
        ('loyalty', 'Loyalty'),
        ('membership', 'Membership'),
        ('government_health_id', 'Government Health ID'),
        ('vaccination_pass', 'Vaccination Pass'),
        ('other', 'Other'),
    ]
    BARCODE_TYPE_CHOICES = [
        ('qr', 'QR'),
        ('barcode', 'Barcode'),
        ('none', 'None'),
    ]

    wallet_account_id = models.UUIDField(db_index=True)
    card_type = models.CharField(max_length=30, choices=CARD_TYPE_CHOICES)
    card_title = models.CharField(max_length=200)
    card_number = models.CharField(max_length=100, blank=True)
    issuer_name = models.CharField(max_length=255)
    issuer_logo_url = models.URLField(max_length=2000, blank=True)
    holder_name = models.CharField(max_length=255)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    card_data = models.JSONField(default=dict)
    barcode_type = models.CharField(max_length=10, choices=BARCODE_TYPE_CHOICES, blank=True)
    barcode_value = models.CharField(max_length=500, blank=True)
    card_image_url = models.URLField(max_length=2000, blank=True)
    background_color = models.CharField(max_length=20, default='#1A56DB')
    text_color = models.CharField(max_length=20, default='#FFFFFF')
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'cymed_portal_digital_cards'
        indexes = [
            models.Index(fields=['wallet_account_id', 'card_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.card_title} ({self.card_type})"


class HealthPass(BaseModel):
    PASS_TYPE_CHOICES = [
        ('vaccination', 'Vaccination'),
        ('covid_test', 'COVID Test'),
        ('immunity', 'Immunity'),
        ('health_declaration', 'Health Declaration'),
        ('travel_health', 'Travel Health'),
    ]
    STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    pass_type = models.CharField(max_length=30, choices=PASS_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    issuer_name = models.CharField(max_length=255)
    pass_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='valid')
    qr_code_data = models.TextField(blank=True)
    pass_data = models.JSONField(default=dict)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_portal_health_passes'
        indexes = [
            models.Index(fields=['account_id', 'pass_type', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.pass_type}) - {self.status}"


class VaccinationRecord(BaseModel):
    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    vaccine_name = models.CharField(max_length=255)
    vaccine_name_ar = models.CharField(max_length=255, blank=True)
    vaccine_code = models.CharField(max_length=50, blank=True)
    cvx_code = models.CharField(max_length=10, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    dose_number = models.PositiveSmallIntegerField(default=1)
    total_doses_required = models.PositiveSmallIntegerField(default=1)
    administered_date = models.DateField()
    administered_by = models.CharField(max_length=255, blank=True)
    facility_name = models.CharField(max_length=255, blank=True)
    site = models.CharField(max_length=50, blank=True)
    route = models.CharField(max_length=50, blank=True)
    next_dose_date = models.DateField(null=True, blank=True)
    certificate_url = models.URLField(max_length=2000, blank=True)
    cymed_immunization_id = models.UUIDField(null=True, blank=True)
    fhir_immunization_id = models.CharField(max_length=255, blank=True, db_index=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'cymed_portal_vaccination_records'
        indexes = [
            models.Index(fields=['account_id', 'vaccine_code', 'administered_date']),
        ]

    def __str__(self):
        return f"{self.vaccine_name} - Dose {self.dose_number} ({self.administered_date})"
