import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='HealthWallet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True, unique=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('wallet_name', models.CharField(default='My Health Wallet', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('card_count', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'db_table': 'cymed_portal_health_wallets',
            },
        ),
        migrations.CreateModel(
            name='DigitalCard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('wallet_account_id', models.UUIDField(db_index=True)),
                ('card_type', models.CharField(
                    choices=[
                        ('patient_id', 'Patient ID'),
                        ('insurance', 'Insurance'),
                        ('loyalty', 'Loyalty'),
                        ('membership', 'Membership'),
                        ('government_health_id', 'Government Health ID'),
                        ('vaccination_pass', 'Vaccination Pass'),
                        ('other', 'Other'),
                    ],
                    max_length=30,
                )),
                ('card_title', models.CharField(max_length=200)),
                ('card_number', models.CharField(blank=True, max_length=100)),
                ('issuer_name', models.CharField(max_length=255)),
                ('issuer_logo_url', models.URLField(blank=True, max_length=2000)),
                ('holder_name', models.CharField(max_length=255)),
                ('valid_from', models.DateField(blank=True, null=True)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('card_data', models.JSONField(default=dict)),
                ('barcode_type', models.CharField(
                    blank=True,
                    choices=[
                        ('qr', 'QR'),
                        ('barcode', 'Barcode'),
                        ('none', 'None'),
                    ],
                    max_length=10,
                )),
                ('barcode_value', models.CharField(blank=True, max_length=500)),
                ('card_image_url', models.URLField(blank=True, max_length=2000)),
                ('background_color', models.CharField(default='#1A56DB', max_length=20)),
                ('text_color', models.CharField(default='#FFFFFF', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'db_table': 'cymed_portal_digital_cards',
            },
        ),
        migrations.CreateModel(
            name='HealthPass',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('pass_type', models.CharField(
                    choices=[
                        ('vaccination', 'Vaccination'),
                        ('covid_test', 'COVID Test'),
                        ('immunity', 'Immunity'),
                        ('health_declaration', 'Health Declaration'),
                        ('travel_health', 'Travel Health'),
                    ],
                    max_length=30,
                )),
                ('title', models.CharField(max_length=200)),
                ('issue_date', models.DateField()),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('issuer_name', models.CharField(max_length=255)),
                ('pass_number', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(
                    choices=[
                        ('valid', 'Valid'),
                        ('expired', 'Expired'),
                        ('revoked', 'Revoked'),
                    ],
                    default='valid',
                    max_length=10,
                )),
                ('qr_code_data', models.TextField(blank=True)),
                ('pass_data', models.JSONField(default=dict)),
                ('is_verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_portal_health_passes',
            },
        ),
        migrations.CreateModel(
            name='VaccinationRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('vaccine_name', models.CharField(max_length=255)),
                ('vaccine_name_ar', models.CharField(blank=True, max_length=255)),
                ('vaccine_code', models.CharField(blank=True, max_length=50)),
                ('cvx_code', models.CharField(blank=True, max_length=10)),
                ('manufacturer', models.CharField(blank=True, max_length=255)),
                ('lot_number', models.CharField(blank=True, max_length=100)),
                ('dose_number', models.PositiveSmallIntegerField(default=1)),
                ('total_doses_required', models.PositiveSmallIntegerField(default=1)),
                ('administered_date', models.DateField()),
                ('administered_by', models.CharField(blank=True, max_length=255)),
                ('facility_name', models.CharField(blank=True, max_length=255)),
                ('site', models.CharField(blank=True, max_length=50)),
                ('route', models.CharField(blank=True, max_length=50)),
                ('next_dose_date', models.DateField(blank=True, null=True)),
                ('certificate_url', models.URLField(blank=True, max_length=2000)),
                ('cymed_immunization_id', models.UUIDField(blank=True, null=True)),
                ('fhir_immunization_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('is_verified', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'cymed_portal_vaccination_records',
            },
        ),
        migrations.AddIndex(
            model_name='digitalcard',
            index=models.Index(fields=['wallet_account_id', 'card_type', 'is_active'], name='cymed_portal_dcard_wallet_idx'),
        ),
        migrations.AddIndex(
            model_name='healthpass',
            index=models.Index(fields=['account_id', 'pass_type', 'status'], name='cymed_portal_hpass_acct_idx'),
        ),
        migrations.AddIndex(
            model_name='vaccinationrecord',
            index=models.Index(fields=['account_id', 'vaccine_code', 'administered_date'], name='cymed_portal_vacc_acct_idx'),
        ),
    ]
