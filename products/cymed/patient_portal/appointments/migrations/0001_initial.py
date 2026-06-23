import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PortalAppointmentRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('is_for_dependent', models.BooleanField(default=False)),
                ('dependent_patient_id', models.UUIDField(blank=True, null=True)),
                ('provider_type', models.CharField(
                    choices=[('hospital', 'Hospital'), ('clinic', 'Clinic'), ('telemedicine', 'Telemedicine')],
                    default='clinic',
                    max_length=20,
                )),
                ('provider_id', models.UUIDField(blank=True, null=True)),
                ('provider_name', models.CharField(blank=True, max_length=255)),
                ('specialty', models.CharField(blank=True, max_length=100)),
                ('physician_id', models.UUIDField(blank=True, null=True)),
                ('physician_name', models.CharField(blank=True, max_length=255)),
                ('preferred_date_1', models.DateField(blank=True, null=True)),
                ('preferred_date_2', models.DateField(blank=True, null=True)),
                ('preferred_date_3', models.DateField(blank=True, null=True)),
                ('preferred_time_slot', models.CharField(
                    choices=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ('evening', 'Evening'), ('any', 'Any')],
                    default='any',
                    max_length=20,
                )),
                ('appointment_type', models.CharField(
                    choices=[
                        ('consultation', 'Consultation'),
                        ('follow_up', 'Follow Up'),
                        ('procedure', 'Procedure'),
                        ('vaccination', 'Vaccination'),
                        ('checkup', 'Checkup'),
                        ('telemedicine', 'Telemedicine'),
                        ('home_visit', 'Home Visit'),
                    ],
                    default='consultation',
                    max_length=20,
                )),
                ('chief_complaint', models.TextField(blank=True)),
                ('insurance_id', models.UUIDField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('confirmed', 'Confirmed'),
                        ('rescheduled', 'Rescheduled'),
                        ('cancelled', 'Cancelled'),
                        ('completed', 'Completed'),
                        ('no_show', 'No Show'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('confirmed_datetime', models.DateTimeField(blank=True, null=True)),
                ('confirmed_location', models.CharField(blank=True, max_length=500)),
                ('cymed_appointment_id', models.UUIDField(blank=True, null=True)),
                ('cancellation_reason', models.TextField(blank=True)),
                ('cancelled_by', models.CharField(
                    blank=True,
                    choices=[('patient', 'Patient'), ('provider', 'Provider'), ('system', 'System')],
                    max_length=20,
                )),
                ('reminder_sent', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'cymed_portal_appointment_requests',
            },
        ),
        migrations.CreateModel(
            name='WaitlistEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('provider_id', models.UUIDField(db_index=True)),
                ('specialty', models.CharField(blank=True, max_length=100)),
                ('physician_id', models.UUIDField(blank=True, null=True)),
                ('waitlist_type', models.CharField(
                    choices=[
                        ('next_available', 'Next Available'),
                        ('specific_physician', 'Specific Physician'),
                        ('specific_date', 'Specific Date'),
                    ],
                    default='next_available',
                    max_length=30,
                )),
                ('earliest_date', models.DateField(blank=True, null=True)),
                ('latest_date', models.DateField(blank=True, null=True)),
                ('priority', models.CharField(
                    choices=[('routine', 'Routine'), ('urgent', 'Urgent'), ('stat', 'Stat')],
                    default='routine',
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('waiting', 'Waiting'),
                        ('offered', 'Offered'),
                        ('accepted', 'Accepted'),
                        ('expired', 'Expired'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='waiting',
                    max_length=20,
                )),
                ('offered_slot', models.DateTimeField(blank=True, null=True)),
                ('offer_expires_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'cymed_portal_waitlist',
            },
        ),
        migrations.CreateModel(
            name='AppointmentReminder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment_request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reminders',
                    to='cymed_portal_appointments.portalappointmentrequest',
                )),
                ('reminder_type', models.CharField(
                    choices=[('email', 'Email'), ('sms', 'SMS'), ('push', 'Push'), ('in_app', 'In App')],
                    default='push',
                    max_length=20,
                )),
                ('scheduled_at', models.DateTimeField()),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('cancelled', 'Cancelled')],
                    default='pending',
                    max_length=20,
                )),
                ('reminder_hours_before', models.PositiveSmallIntegerField(default=24)),
            ],
            options={
                'db_table': 'cymed_portal_appointment_reminders',
            },
        ),
        migrations.CreateModel(
            name='AppointmentRating',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('appointment_request', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rating',
                    to='cymed_portal_appointments.portalappointmentrequest',
                )),
                ('account_id', models.UUIDField(db_index=True)),
                ('overall_rating', models.PositiveSmallIntegerField()),
                ('wait_time_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('staff_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('facility_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('physician_rating', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('comment', models.TextField(blank=True)),
                ('would_recommend', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cymed_portal_appointment_ratings',
            },
        ),
        migrations.AddIndex(
            model_name='portalappointmentrequest',
            index=models.Index(fields=['account_id', 'status'], name='cymed_appt_req_acct_status_idx'),
        ),
        migrations.AddIndex(
            model_name='portalappointmentrequest',
            index=models.Index(fields=['patient_id', 'status'], name='cymed_appt_req_patient_status_idx'),
        ),
        migrations.AddIndex(
            model_name='portalappointmentrequest',
            index=models.Index(fields=['provider_id', 'preferred_date_1'], name='cymed_appt_req_provider_date_idx'),
        ),
        migrations.AddIndex(
            model_name='waitlistentry',
            index=models.Index(fields=['account_id', 'status'], name='cymed_waitlist_acct_status_idx'),
        ),
        migrations.AddIndex(
            model_name='waitlistentry',
            index=models.Index(fields=['provider_id', 'status'], name='cymed_waitlist_provider_status_idx'),
        ),
    ]
