import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='TelemedicineSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('appointment_request_id', models.UUIDField(blank=True, null=True)),
                ('cymed_telemedicine_id', models.UUIDField(blank=True, null=True)),
                ('provider_id', models.UUIDField(db_index=True)),
                ('provider_name', models.CharField(max_length=255)),
                ('session_type', models.CharField(
                    choices=[('video', 'Video'), ('audio', 'Audio'), ('chat', 'Chat')],
                    default='video',
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('scheduled', 'Scheduled'),
                        ('waiting', 'Waiting'),
                        ('in_progress', 'In Progress'),
                        ('completed', 'Completed'),
                        ('missed', 'Missed'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='scheduled',
                    max_length=20,
                )),
                ('scheduled_at', models.DateTimeField()),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('duration_minutes', models.PositiveSmallIntegerField(default=0)),
                ('meeting_url', models.URLField(blank=True, max_length=2000)),
                ('meeting_id', models.CharField(blank=True, max_length=255)),
                ('meeting_password', models.CharField(blank=True, max_length=100)),
                ('patient_joined_at', models.DateTimeField(blank=True, null=True)),
                ('provider_joined_at', models.DateTimeField(blank=True, null=True)),
                ('chief_complaint', models.TextField(blank=True)),
                ('session_notes_available', models.BooleanField(default=False)),
                ('follow_up_required', models.BooleanField(default=False)),
                ('follow_up_date', models.DateField(blank=True, null=True)),
                ('rating', models.PositiveSmallIntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_portal_telemedicine_sessions',
            },
        ),
        migrations.CreateModel(
            name='TelemedicineDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='documents',
                    to='cymed_portal_telemedicine.telemedicinesession',
                )),
                ('document_type', models.CharField(
                    choices=[
                        ('lab_result', 'Lab Result'),
                        ('imaging', 'Imaging'),
                        ('referral', 'Referral'),
                        ('previous_report', 'Previous Report'),
                        ('prescription', 'Prescription'),
                        ('other', 'Other'),
                    ],
                    default='other',
                    max_length=30,
                )),
                ('file_name', models.CharField(max_length=255)),
                ('file_url', models.URLField(max_length=2000)),
                ('file_size_bytes', models.PositiveBigIntegerField(default=0)),
                ('file_type', models.CharField(max_length=50)),
                ('uploaded_by', models.CharField(
                    choices=[('patient', 'Patient'), ('provider', 'Provider')],
                    default='patient',
                    max_length=20,
                )),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'cymed_portal_tele_documents',
            },
        ),
        migrations.CreateModel(
            name='TelemedicineChat',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='chat_messages',
                    to='cymed_portal_telemedicine.telemedicinesession',
                )),
                ('sender_type', models.CharField(
                    choices=[('patient', 'Patient'), ('provider', 'Provider'), ('system', 'System')],
                    default='patient',
                    max_length=20,
                )),
                ('sender_id', models.UUIDField()),
                ('message', models.TextField()),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('is_system_message', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'cymed_portal_tele_chat',
                'ordering': ['-sent_at'],
            },
        ),
        migrations.CreateModel(
            name='TelemedicineRating',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='session_rating',
                    to='cymed_portal_telemedicine.telemedicinesession',
                )),
                ('account_id', models.UUIDField(db_index=True)),
                ('overall_rating', models.PositiveSmallIntegerField()),
                ('audio_quality_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('video_quality_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('provider_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('comment', models.TextField(blank=True)),
                ('would_use_again', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cymed_portal_tele_ratings',
            },
        ),
        migrations.AddIndex(
            model_name='telemedicinesession',
            index=models.Index(fields=['account_id', 'status'], name='cymed_tele_sess_acct_status_idx'),
        ),
        migrations.AddIndex(
            model_name='telemedicinesession',
            index=models.Index(fields=['provider_id', 'scheduled_at'], name='cymed_tele_sess_provider_date_idx'),
        ),
    ]
