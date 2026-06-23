from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='HealthTimeline',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('timeline_name', models.CharField(default='My Health Timeline', max_length=200)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('total_events', models.PositiveIntegerField(default=0)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'cymed_portal_health_timelines',
            },
        ),
        migrations.CreateModel(
            name='PatientJourney',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('journey_name', models.CharField(max_length=200)),
                ('journey_type', models.CharField(
                    choices=[
                        ('chronic_condition', 'Chronic Condition'),
                        ('surgical', 'Surgical'),
                        ('maternity', 'Maternity'),
                        ('cancer_care', 'Cancer Care'),
                        ('rehabilitation', 'Rehabilitation'),
                        ('preventive', 'Preventive'),
                        ('general', 'General'),
                    ],
                    max_length=20,
                )),
                ('primary_diagnosis', models.CharField(blank=True, max_length=255)),
                ('icd11_code', models.CharField(blank=True, max_length=20)),
                ('start_date', models.DateField()),
                ('expected_end_date', models.DateField(blank=True, null=True)),
                ('actual_end_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Active'),
                        ('completed', 'Completed'),
                        ('paused', 'Paused'),
                        ('discontinued', 'Discontinued'),
                    ],
                    default='active',
                    max_length=20,
                )),
                ('care_team', models.JSONField(default=list)),
                ('goals', models.JSONField(default=list)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'cymed_portal_patient_journeys',
            },
        ),
        migrations.CreateModel(
            name='HealthTimelineEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('timeline', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='events',
                    to='cymed_portal_health_journey.healthtimeline',
                )),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('event_type', models.CharField(
                    choices=[
                        ('appointment', 'Appointment'),
                        ('lab_result', 'Lab Result'),
                        ('imaging', 'Imaging'),
                        ('prescription', 'Prescription'),
                        ('hospitalization', 'Hospitalization'),
                        ('vaccination', 'Vaccination'),
                        ('diagnosis', 'Diagnosis'),
                        ('procedure', 'Procedure'),
                        ('telemedicine', 'Telemedicine'),
                        ('note', 'Note'),
                    ],
                    max_length=20,
                )),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('provider_name', models.CharField(blank=True, max_length=255)),
                ('facility_name', models.CharField(blank=True, max_length=255)),
                ('event_date', models.DateField(db_index=True)),
                ('source_id', models.UUIDField(blank=True, null=True)),
                ('source_type', models.CharField(blank=True, max_length=50)),
                ('is_pinned', models.BooleanField(default=False)),
                ('attachments', models.JSONField(default=list)),
            ],
            options={
                'db_table': 'cymed_portal_timeline_events',
            },
        ),
        migrations.CreateModel(
            name='HealthMilestone',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('journey', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='milestones',
                    to='cymed_portal_health_journey.patientjourney',
                )),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('milestone_type', models.CharField(
                    choices=[
                        ('diagnosis', 'Diagnosis'),
                        ('treatment_start', 'Treatment Start'),
                        ('surgery', 'Surgery'),
                        ('first_chemo', 'First Chemotherapy'),
                        ('remission', 'Remission'),
                        ('discharge', 'Discharge'),
                        ('goal_achieved', 'Goal Achieved'),
                        ('custom', 'Custom'),
                    ],
                    max_length=20,
                )),
                ('milestone_date', models.DateField()),
                ('is_achieved', models.BooleanField(default=False)),
                ('achieved_at', models.DateTimeField(blank=True, null=True)),
                ('is_shared', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'cymed_portal_health_milestones',
            },
        ),
        migrations.CreateModel(
            name='CareEpisode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('journey', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='episodes',
                    to='cymed_portal_health_journey.patientjourney',
                )),
                ('episode_type', models.CharField(
                    choices=[
                        ('inpatient', 'Inpatient'),
                        ('outpatient', 'Outpatient'),
                        ('emergency', 'Emergency'),
                        ('telemedicine', 'Telemedicine'),
                        ('home_care', 'Home Care'),
                    ],
                    max_length=20,
                )),
                ('facility_name', models.CharField(max_length=255)),
                ('facility_id', models.UUIDField(blank=True, null=True)),
                ('admission_date', models.DateField()),
                ('discharge_date', models.DateField(blank=True, null=True)),
                ('primary_diagnosis', models.CharField(blank=True, max_length=255)),
                ('icd11_code', models.CharField(blank=True, max_length=20)),
                ('attending_physician', models.CharField(blank=True, max_length=255)),
                ('discharge_summary', models.TextField(blank=True)),
                ('follow_up_instructions', models.TextField(blank=True)),
                ('cymed_encounter_id', models.UUIDField(blank=True, null=True)),
                ('cymed_admission_id', models.UUIDField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_portal_care_episodes',
            },
        ),
        migrations.AlterUniqueTogether(
            name='healthtimeline',
            unique_together={('tenant_id', 'patient_id')},
        ),
        migrations.AddIndex(
            model_name='healthtimelineevent',
            index=models.Index(
                fields=['timeline', 'event_date'],
                name='timeline_events_timeline_date_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='healthtimelineevent',
            index=models.Index(
                fields=['account_id', 'event_type'],
                name='timeline_events_acct_type_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='patientjourney',
            index=models.Index(
                fields=['account_id', 'status'],
                name='patient_journeys_acct_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='healthmilestone',
            index=models.Index(
                fields=['journey', 'is_achieved'],
                name='health_milestones_journey_achieved_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='careepisode',
            index=models.Index(
                fields=['account_id', 'episode_type', 'admission_date'],
                name='care_episodes_acct_type_date_idx',
            ),
        ),
    ]
