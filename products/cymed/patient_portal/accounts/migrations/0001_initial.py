import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PatientPortalAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('cyidentity_user_id', models.UUIDField(db_index=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('username', models.CharField(max_length=150, unique=True)),
                ('account_status', models.CharField(
                    choices=[
                        ('active', 'Active'),
                        ('inactive', 'Inactive'),
                        ('suspended', 'Suspended'),
                        ('pending_verification', 'Pending Verification'),
                    ],
                    default='pending_verification',
                    max_length=30,
                )),
                ('is_email_verified', models.BooleanField(default=False)),
                ('is_phone_verified', models.BooleanField(default=False)),
                ('email_verified_at', models.DateTimeField(blank=True, null=True)),
                ('phone_verified_at', models.DateTimeField(blank=True, null=True)),
                ('last_login_at', models.DateTimeField(blank=True, null=True)),
                ('login_count', models.PositiveIntegerField(default=0)),
                ('registration_source', models.CharField(
                    choices=[
                        ('web', 'Web'),
                        ('mobile', 'Mobile'),
                        ('clinic', 'Clinic'),
                        ('hospital', 'Hospital'),
                        ('self_registration', 'Self Registration'),
                    ],
                    default='self_registration',
                    max_length=30,
                )),
                ('referred_by', models.UUIDField(blank=True, null=True)),
                ('preferred_language', models.CharField(default='en', max_length=10)),
                ('timezone', models.CharField(default='UTC', max_length=50)),
                ('profile_photo_url', models.URLField(blank=True, max_length=2000)),
            ],
            options={
                'db_table': 'cymed_portal_accounts',
            },
        ),
        migrations.AddIndex(
            model_name='patientportalaccount',
            index=models.Index(fields=['patient_id'], name='cymed_porta_patient_idx'),
        ),
        migrations.AddIndex(
            model_name='patientportalaccount',
            index=models.Index(fields=['email'], name='cymed_porta_email_idx'),
        ),
        migrations.AddIndex(
            model_name='patientportalaccount',
            index=models.Index(fields=['account_status'], name='cymed_porta_status_idx'),
        ),
        migrations.CreateModel(
            name='PatientProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to='cymed_portal_accounts.patientportalaccount',
                )),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('first_name_ar', models.CharField(blank=True, max_length=150)),
                ('last_name_ar', models.CharField(blank=True, max_length=150)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(
                    blank=True,
                    choices=[
                        ('male', 'Male'),
                        ('female', 'Female'),
                        ('other', 'Other'),
                        ('prefer_not_to_say', 'Prefer Not to Say'),
                    ],
                    max_length=20,
                )),
                ('national_id', models.CharField(blank=True, db_index=True, max_length=50)),
                ('passport_number', models.CharField(blank=True, max_length=50)),
                ('nationality', models.CharField(blank=True, max_length=3)),
                ('blood_group', models.CharField(
                    choices=[
                        ('A+', 'A+'),
                        ('A-', 'A-'),
                        ('B+', 'B+'),
                        ('B-', 'B-'),
                        ('AB+', 'AB+'),
                        ('AB-', 'AB-'),
                        ('O+', 'O+'),
                        ('O-', 'O-'),
                        ('unknown', 'Unknown'),
                    ],
                    default='unknown',
                    max_length=10,
                )),
                ('address_line1', models.CharField(blank=True, max_length=255)),
                ('address_line2', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('country', models.CharField(blank=True, max_length=3)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('emergency_contact_name', models.CharField(blank=True, max_length=200)),
                ('emergency_contact_phone', models.CharField(blank=True, max_length=30)),
                ('emergency_contact_relationship', models.CharField(blank=True, max_length=50)),
            ],
            options={
                'db_table': 'cymed_portal_profiles',
            },
        ),
        migrations.CreateModel(
            name='PatientPreferences',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='preferences',
                    to='cymed_portal_accounts.patientportalaccount',
                )),
                ('preferred_language', models.CharField(default='en', max_length=10)),
                ('preferred_currency', models.CharField(default='USD', max_length=3)),
                ('email_notifications', models.BooleanField(default=True)),
                ('sms_notifications', models.BooleanField(default=True)),
                ('push_notifications', models.BooleanField(default=True)),
                ('appointment_reminders', models.BooleanField(default=True)),
                ('lab_result_alerts', models.BooleanField(default=True)),
                ('prescription_alerts', models.BooleanField(default=True)),
                ('marketing_communications', models.BooleanField(default=False)),
                ('data_sharing_research', models.BooleanField(default=False)),
                ('newsletter', models.BooleanField(default=False)),
                ('preferred_appointment_time', models.CharField(
                    choices=[
                        ('morning', 'Morning'),
                        ('afternoon', 'Afternoon'),
                        ('evening', 'Evening'),
                        ('any', 'Any'),
                    ],
                    default='any',
                    max_length=20,
                )),
                ('preferred_provider_gender', models.CharField(
                    choices=[
                        ('any', 'Any'),
                        ('male', 'Male'),
                        ('female', 'Female'),
                    ],
                    default='any',
                    max_length=10,
                )),
            ],
            options={
                'db_table': 'cymed_portal_preferences',
            },
        ),
        migrations.CreateModel(
            name='PatientSecuritySettings',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='security_settings',
                    to='cymed_portal_accounts.patientportalaccount',
                )),
                ('mfa_enabled', models.BooleanField(default=False)),
                ('mfa_method', models.CharField(
                    choices=[
                        ('totp', 'TOTP'),
                        ('sms', 'SMS'),
                        ('email', 'Email'),
                        ('authenticator_app', 'Authenticator App'),
                    ],
                    default='sms',
                    max_length=20,
                )),
                ('biometric_enabled', models.BooleanField(default=False)),
                ('passkey_enabled', models.BooleanField(default=False)),
                ('login_notifications', models.BooleanField(default=True)),
                ('trusted_devices_enabled', models.BooleanField(default=True)),
                ('session_timeout_minutes', models.PositiveSmallIntegerField(default=30)),
                ('failed_login_count', models.PositiveSmallIntegerField(default=0)),
                ('locked_until', models.DateTimeField(blank=True, null=True)),
                ('last_password_change', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_portal_security_settings',
            },
        ),
        migrations.CreateModel(
            name='PatientDevice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='devices',
                    to='cymed_portal_accounts.patientportalaccount',
                )),
                ('device_name', models.CharField(max_length=255)),
                ('device_type', models.CharField(
                    choices=[
                        ('ios', 'iOS'),
                        ('android', 'Android'),
                        ('web', 'Web'),
                        ('tablet', 'Tablet'),
                    ],
                    default='web',
                    max_length=20,
                )),
                ('device_token', models.CharField(blank=True, max_length=500)),
                ('device_fingerprint', models.CharField(blank=True, db_index=True, max_length=255)),
                ('platform_version', models.CharField(blank=True, max_length=50)),
                ('app_version', models.CharField(blank=True, max_length=20)),
                ('is_trusted', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'cymed_portal_devices',
            },
        ),
        migrations.AddIndex(
            model_name='patientdevice',
            index=models.Index(fields=['account', 'is_active'], name='cymed_porta_dev_active_idx'),
        ),
    ]
