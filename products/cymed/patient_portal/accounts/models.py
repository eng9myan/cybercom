import uuid
from django.db import models
from platform.common.models import BaseModel


class PatientPortalAccount(BaseModel):
    ACCOUNT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending_verification', 'Pending Verification'),
    ]

    REGISTRATION_SOURCE_CHOICES = [
        ('web', 'Web'),
        ('mobile', 'Mobile'),
        ('clinic', 'Clinic'),
        ('hospital', 'Hospital'),
        ('self_registration', 'Self Registration'),
    ]

    patient_id = models.UUIDField(db_index=True)
    cyidentity_user_id = models.UUIDField(db_index=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    username = models.CharField(max_length=150, unique=True)
    account_status = models.CharField(
        max_length=30,
        choices=ACCOUNT_STATUS_CHOICES,
        default='pending_verification',
    )
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)
    registration_source = models.CharField(
        max_length=30,
        choices=REGISTRATION_SOURCE_CHOICES,
        default='self_registration',
    )
    referred_by = models.UUIDField(null=True, blank=True)
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    profile_photo_url = models.URLField(max_length=2000, blank=True)

    class Meta:
        db_table = 'cymed_portal_accounts'
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['email']),
            models.Index(fields=['account_status']),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"


class PatientProfile(BaseModel):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer Not to Say'),
    ]

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('unknown', 'Unknown'),
    ]

    account = models.OneToOneField(
        PatientPortalAccount,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    first_name_ar = models.CharField(max_length=150, blank=True)
    last_name_ar = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    national_id = models.CharField(max_length=50, blank=True, db_index=True)
    passport_number = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=3, blank=True)
    blood_group = models.CharField(
        max_length=10,
        choices=BLOOD_GROUP_CHOICES,
        default='unknown',
    )
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=3, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'cymed_portal_profiles'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class PatientPreferences(BaseModel):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('es', 'Spanish'),
    ]

    APPOINTMENT_TIME_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('any', 'Any'),
    ]

    PROVIDER_GENDER_CHOICES = [
        ('any', 'Any'),
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    account = models.OneToOneField(
        PatientPortalAccount,
        on_delete=models.CASCADE,
        related_name='preferences',
    )
    preferred_language = models.CharField(max_length=10, default='en')
    preferred_currency = models.CharField(max_length=3, default='USD')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    appointment_reminders = models.BooleanField(default=True)
    lab_result_alerts = models.BooleanField(default=True)
    prescription_alerts = models.BooleanField(default=True)
    marketing_communications = models.BooleanField(default=False)
    data_sharing_research = models.BooleanField(default=False)
    newsletter = models.BooleanField(default=False)
    preferred_appointment_time = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TIME_CHOICES,
        default='any',
    )
    preferred_provider_gender = models.CharField(
        max_length=10,
        choices=PROVIDER_GENDER_CHOICES,
        default='any',
    )

    class Meta:
        db_table = 'cymed_portal_preferences'

    def __str__(self):
        return f"Preferences for {self.account.username}"


class PatientSecuritySettings(BaseModel):
    MFA_METHOD_CHOICES = [
        ('totp', 'TOTP'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('authenticator_app', 'Authenticator App'),
    ]

    account = models.OneToOneField(
        PatientPortalAccount,
        on_delete=models.CASCADE,
        related_name='security_settings',
    )
    mfa_enabled = models.BooleanField(default=False)
    mfa_method = models.CharField(
        max_length=20,
        choices=MFA_METHOD_CHOICES,
        default='sms',
    )
    biometric_enabled = models.BooleanField(default=False)
    passkey_enabled = models.BooleanField(default=False)
    login_notifications = models.BooleanField(default=True)
    trusted_devices_enabled = models.BooleanField(default=True)
    session_timeout_minutes = models.PositiveSmallIntegerField(default=30)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_portal_security_settings'

    def __str__(self):
        return f"Security settings for {self.account.username}"


class PatientDevice(BaseModel):
    DEVICE_TYPE_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
        ('tablet', 'Tablet'),
    ]

    account = models.ForeignKey(
        PatientPortalAccount,
        on_delete=models.CASCADE,
        related_name='devices',
    )
    device_name = models.CharField(max_length=255)
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default='web',
    )
    device_token = models.CharField(max_length=500, blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True, db_index=True)
    platform_version = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=20, blank=True)
    is_trusted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cymed_portal_devices'
        indexes = [
            models.Index(fields=['account', 'is_active']),
        ]

    def __str__(self):
        return f"{self.device_name} ({self.device_type}) - {self.account.username}"
