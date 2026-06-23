import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='MessageThread',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('thread_type', models.CharField(
                    choices=[
                        ('provider_message', 'Provider Message'),
                        ('appointment_inquiry', 'Appointment Inquiry'),
                        ('prescription_inquiry', 'Prescription Inquiry'),
                        ('lab_inquiry', 'Lab Inquiry'),
                        ('billing_inquiry', 'Billing Inquiry'),
                        ('support', 'Support'),
                        ('general', 'General'),
                    ],
                    default='general',
                    max_length=30,
                )),
                ('subject', models.CharField(max_length=255)),
                ('provider_id', models.UUIDField(blank=True, null=True)),
                ('provider_name', models.CharField(blank=True, max_length=255)),
                ('facility_id', models.UUIDField(blank=True, null=True)),
                ('facility_name', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(
                    choices=[
                        ('open', 'Open'),
                        ('closed', 'Closed'),
                        ('archived', 'Archived'),
                    ],
                    default='open',
                    max_length=20,
                )),
                ('is_urgent', models.BooleanField(default=False)),
                ('last_message_at', models.DateTimeField(blank=True, null=True)),
                ('message_count', models.PositiveIntegerField(default=0)),
                ('unread_count', models.PositiveIntegerField(default=0)),
                ('cyconnect_thread_id', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'db_table': 'cymed_portal_message_threads',
            },
        ),
        migrations.CreateModel(
            name='PatientMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('thread', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='cymed_portal_messaging.messagethread',
                )),
                ('account_id', models.UUIDField(db_index=True)),
                ('sender_type', models.CharField(
                    choices=[
                        ('patient', 'Patient'),
                        ('provider', 'Provider'),
                        ('system', 'System'),
                    ],
                    default='patient',
                    max_length=10,
                )),
                ('sender_id', models.UUIDField()),
                ('sender_name', models.CharField(blank=True, max_length=255)),
                ('body', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('is_system_message', models.BooleanField(default=False)),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'cymed_portal_messages',
                'ordering': ['-sent_at'],
            },
        ),
        migrations.CreateModel(
            name='MessageAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('message', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='cymed_portal_messaging.patientmessage',
                )),
                ('account_id', models.UUIDField(db_index=True)),
                ('file_name', models.CharField(max_length=255)),
                ('file_url', models.URLField(max_length=2000)),
                ('file_type', models.CharField(max_length=50)),
                ('file_size_bytes', models.PositiveBigIntegerField(default=0)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'cymed_portal_message_attachments',
            },
        ),
        migrations.CreateModel(
            name='SecureMessageRecipient',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('thread', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='recipients',
                    to='cymed_portal_messaging.messagethread',
                )),
                ('recipient_type', models.CharField(
                    choices=[
                        ('patient', 'Patient'),
                        ('provider', 'Provider'),
                        ('support_team', 'Support Team'),
                    ],
                    max_length=20,
                )),
                ('recipient_id', models.UUIDField(db_index=True)),
                ('recipient_name', models.CharField(blank=True, max_length=255)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cymed_portal_message_recipients',
            },
        ),
        migrations.AddIndex(
            model_name='messagethread',
            index=models.Index(fields=['account_id', 'status', 'last_message_at'], name='cymed_portal_thread_acct_idx'),
        ),
        migrations.AddIndex(
            model_name='patientmessage',
            index=models.Index(fields=['thread', 'is_read'], name='cymed_portal_msg_thread_read_idx'),
        ),
        migrations.AddIndex(
            model_name='securemessagerecipient',
            index=models.Index(fields=['thread', 'recipient_id'], name='cymed_portal_recip_thread_idx'),
        ),
    ]
