import uuid
from django.db import models
from platform.common.models import BaseModel


class PortalConsentType(BaseModel):
    CONSENT_CATEGORY_CHOICES = [
        ('treatment', 'Treatment'),
        ('research', 'Research'),
        ('data_sharing', 'Data Sharing'),
        ('telemedicine', 'Telemedicine'),
        ('marketing', 'Marketing'),
        ('general', 'General'),
    ]

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    consent_category = models.CharField(max_length=20, choices=CONSENT_CATEGORY_CHOICES)
    is_mandatory = models.BooleanField(default=False)
    version = models.CharField(max_length=20, default='1.0')
    content_url = models.URLField(max_length=2000, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'cymed_portal_consent_types'
        ordering = ['consent_category', 'name']

    def __str__(self):
        return f"{self.name} (v{self.version}) [{self.consent_category}]"


class PortalConsentRecord(BaseModel):
    CONSENT_STATUS_CHOICES = [
        ('granted', 'Granted'),
        ('denied', 'Denied'),
        ('withdrawn', 'Withdrawn'),
        ('pending', 'Pending'),
    ]
    CHANNEL_CHOICES = [
        ('portal', 'Portal'),
        ('mobile', 'Mobile'),
        ('kiosk', 'Kiosk'),
        ('paper', 'Paper'),
        ('verbal', 'Verbal'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    consent_type = models.ForeignKey(
        PortalConsentType,
        on_delete=models.PROTECT,
        related_name='records',
    )
    cymed_consent_id = models.UUIDField(null=True, blank=True)
    consent_status = models.CharField(
        max_length=20, choices=CONSENT_STATUS_CHOICES, default='pending'
    )
    granted_at = models.DateTimeField(null=True, blank=True)
    denied_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    version_consented = models.CharField(max_length=20, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    device_id = models.UUIDField(null=True, blank=True)
    channel = models.CharField(
        max_length=20, choices=CHANNEL_CHOICES, default='portal'
    )
    witness_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'cymed_portal_consent_records'
        indexes = [
            models.Index(fields=['account_id', 'consent_type', 'consent_status']),
        ]

    def __str__(self):
        return f"ConsentRecord {self.id} - {self.account_id} [{self.consent_status}]"


class ConsentRequest(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('granted', 'Granted'),
        ('denied', 'Denied'),
        ('expired', 'Expired'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    consent_type = models.ForeignKey(
        PortalConsentType,
        on_delete=models.PROTECT,
        related_name='requests',
    )
    requested_by = models.UUIDField()
    requester_name = models.CharField(max_length=255, blank=True)
    request_reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_portal_consent_requests'
        indexes = [
            models.Index(fields=['account_id', 'status']),
        ]

    def __str__(self):
        return f"ConsentRequest {self.id} - {self.account_id} [{self.status}]"


class ConsentHistory(BaseModel):
    ACTION_CHOICES = [
        ('granted', 'Granted'),
        ('denied', 'Denied'),
        ('withdrawn', 'Withdrawn'),
        ('version_updated', 'Version Updated'),
    ]

    consent_record = models.ForeignKey(
        PortalConsentRecord,
        on_delete=models.CASCADE,
        related_name='history',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.UUIDField()
    reason = models.TextField(blank=True)

    class Meta:
        db_table = 'cymed_portal_consent_history'
        ordering = ['-changed_at']

    def __str__(self):
        return f"ConsentHistory {self.id} - {self.action} on record {self.consent_record_id}"
