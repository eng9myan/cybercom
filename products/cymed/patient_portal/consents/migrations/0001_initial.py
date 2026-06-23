import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PortalConsentType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('name_ar', models.CharField(blank=True, max_length=200)),
                ('description', models.TextField()),
                ('consent_category', models.CharField(
                    choices=[
                        ('treatment', 'Treatment'),
                        ('research', 'Research'),
                        ('data_sharing', 'Data Sharing'),
                        ('telemedicine', 'Telemedicine'),
                        ('marketing', 'Marketing'),
                        ('general', 'General'),
                    ],
                    max_length=20,
                )),
                ('is_mandatory', models.BooleanField(default=False)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('content_url', models.URLField(blank=True, max_length=2000)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cymed_portal_consent_types',
                'ordering': ['consent_category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='PortalConsentRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('consent_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='records',
                    to='cymed_portal_consents.portalconsenttype',
                )),
                ('cymed_consent_id', models.UUIDField(blank=True, null=True)),
                ('consent_status', models.CharField(
                    choices=[
                        ('granted', 'Granted'),
                        ('denied', 'Denied'),
                        ('withdrawn', 'Withdrawn'),
                        ('pending', 'Pending'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('granted_at', models.DateTimeField(blank=True, null=True)),
                ('denied_at', models.DateTimeField(blank=True, null=True)),
                ('withdrawn_at', models.DateTimeField(blank=True, null=True)),
                ('version_consented', models.CharField(blank=True, max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=500)),
                ('device_id', models.UUIDField(blank=True, null=True)),
                ('channel', models.CharField(
                    choices=[
                        ('portal', 'Portal'),
                        ('mobile', 'Mobile'),
                        ('kiosk', 'Kiosk'),
                        ('paper', 'Paper'),
                        ('verbal', 'Verbal'),
                    ],
                    default='portal',
                    max_length=20,
                )),
                ('witness_id', models.UUIDField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'cymed_portal_consent_records',
            },
        ),
        migrations.CreateModel(
            name='ConsentRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('consent_type', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='requests',
                    to='cymed_portal_consents.portalconsenttype',
                )),
                ('requested_by', models.UUIDField()),
                ('requester_name', models.CharField(blank=True, max_length=255)),
                ('request_reason', models.TextField(blank=True)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('granted', 'Granted'),
                        ('denied', 'Denied'),
                        ('expired', 'Expired'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_portal_consent_requests',
            },
        ),
        migrations.CreateModel(
            name='ConsentHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('consent_record', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='history',
                    to='cymed_portal_consents.portalconsentrecord',
                )),
                ('action', models.CharField(
                    choices=[
                        ('granted', 'Granted'),
                        ('denied', 'Denied'),
                        ('withdrawn', 'Withdrawn'),
                        ('version_updated', 'Version Updated'),
                    ],
                    max_length=20,
                )),
                ('previous_status', models.CharField(blank=True, max_length=20)),
                ('new_status', models.CharField(max_length=20)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.UUIDField()),
                ('reason', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'cymed_portal_consent_history',
                'ordering': ['-changed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='portalconsentrecord',
            index=models.Index(fields=['account_id', 'consent_type', 'consent_status'], name='cymed_consent_rec_acct_type_status_idx'),
        ),
        migrations.AddIndex(
            model_name='consentrequest',
            index=models.Index(fields=['account_id', 'status'], name='cymed_consent_req_acct_status_idx'),
        ),
    ]
