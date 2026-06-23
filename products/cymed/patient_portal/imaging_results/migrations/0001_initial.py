from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ImagingResultView',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('cymed_imaging_result_id', models.UUIDField(db_index=True)),
                ('imaging_center_id', models.UUIDField(db_index=True)),
                ('imaging_center_name', models.CharField(max_length=255)),
                ('order_number', models.CharField(blank=True, max_length=100)),
                ('accession_number', models.CharField(blank=True, db_index=True, max_length=100)),
                ('study_date', models.DateField(blank=True, null=True)),
                ('modality', models.CharField(max_length=30)),
                ('body_part', models.CharField(blank=True, max_length=100)),
                ('study_description', models.CharField(blank=True, max_length=500)),
                ('report_status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('preliminary', 'Preliminary'),
                        ('final', 'Final'),
                        ('amended', 'Amended'),
                        ('corrected', 'Corrected'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('radiologist_name', models.CharField(blank=True, max_length=255)),
                ('report_summary', models.TextField(blank=True)),
                ('report_url', models.URLField(blank=True, max_length=2000)),
                ('has_critical_finding', models.BooleanField(default=False)),
                ('is_viewed', models.BooleanField(default=False)),
                ('viewed_at', models.DateTimeField(blank=True, null=True)),
                ('fhir_diagnostic_report_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('fhir_imaging_study_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('dicom_study_instance_uid', models.CharField(blank=True, max_length=255)),
                ('viewer_url', models.URLField(blank=True, max_length=2000)),
            ],
            options={
                'db_table': 'cymed_portal_imaging_results',
            },
        ),
        migrations.CreateModel(
            name='ImagingStudyMetadata',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('imaging_result', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='series',
                    to='cymed_portal_imaging_results.imagingresultview',
                )),
                ('series_number', models.PositiveSmallIntegerField()),
                ('series_description', models.CharField(blank=True, max_length=255)),
                ('modality', models.CharField(max_length=30)),
                ('instance_count', models.PositiveSmallIntegerField(default=0)),
                ('series_instance_uid', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'db_table': 'cymed_portal_imaging_series',
            },
        ),
        migrations.CreateModel(
            name='ImagingReportAccess',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('imaging_result', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='access_log',
                    to='cymed_portal_imaging_results.imagingresultview',
                )),
                ('access_type', models.CharField(
                    choices=[
                        ('view_report', 'View Report'),
                        ('download_report', 'Download Report'),
                        ('view_images', 'View Images'),
                        ('share', 'Share'),
                    ],
                    default='view_report',
                    max_length=20,
                )),
                ('accessed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'cymed_portal_imaging_access',
                'ordering': ['-accessed_at'],
            },
        ),
        migrations.CreateModel(
            name='ImagingShareLink',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('imaging_result', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='share_links',
                    to='cymed_portal_imaging_results.imagingresultview',
                )),
                ('account_id', models.UUIDField(db_index=True)),
                ('share_token', models.CharField(db_index=True, max_length=255, unique=True)),
                ('share_type', models.CharField(
                    choices=[
                        ('report_only', 'Report Only'),
                        ('images_and_report', 'Images and Report'),
                    ],
                    default='report_only',
                    max_length=20,
                )),
                ('shared_with_name', models.CharField(blank=True, max_length=255)),
                ('valid_until', models.DateTimeField()),
                ('access_count', models.PositiveIntegerField(default=0)),
                ('is_revoked', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'cymed_portal_imaging_share_links',
            },
        ),
        migrations.AddIndex(
            model_name='imagingresultview',
            index=models.Index(
                fields=['account_id', 'modality', 'study_date'],
                name='imaging_results_acct_mod_date_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='imagingresultview',
            index=models.Index(
                fields=['patient_id', 'report_status'],
                name='imaging_results_patient_status_idx',
            ),
        ),
    ]
