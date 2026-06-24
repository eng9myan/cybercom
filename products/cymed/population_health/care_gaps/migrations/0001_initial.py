import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CareGap',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('gap_type', models.CharField(choices=[('screening', 'Screening'), ('vaccination', 'Vaccination'), ('follow_up', 'Follow Up'), ('medication_adherence', 'Medication Adherence'), ('lab_test', 'Lab Test'), ('imaging', 'Imaging'), ('preventive', 'Preventive'), ('chronic_monitoring', 'Chronic Monitoring'), ('dental', 'Dental'), ('mental_health', 'Mental Health')], max_length=30)),
                ('gap_description', models.CharField(max_length=500)),
                ('icd11_code', models.CharField(blank=True, max_length=20)),
                ('loinc_code', models.CharField(blank=True, max_length=30)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('last_service_date', models.DateField(blank=True, null=True)),
                ('next_service_due', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('closed', 'Closed'), ('in_progress', 'In Progress'), ('waived', 'Waived'), ('declined', 'Declined')], default='open', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=10)),
                ('identified_by_rule_id', models.UUIDField(blank=True, null=True)),
                ('assigned_provider_id', models.UUIDField(blank=True, null=True)),
                ('source', models.CharField(choices=[('automated', 'Automated'), ('manual', 'Manual'), ('registry', 'Registry'), ('external', 'External')], default='automated', max_length=30)),
            ],
            options={
                'db_table': 'cymed_ph_gap_care_gaps',
            },
        ),
        migrations.CreateModel(
            name='CareGapRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('rule_name', models.CharField(max_length=200)),
                ('rule_code', models.CharField(max_length=50, unique=True)),
                ('gap_type', models.CharField(choices=[('screening', 'Screening'), ('vaccination', 'Vaccination'), ('follow_up', 'Follow Up'), ('medication_adherence', 'Medication Adherence'), ('lab_test', 'Lab Test'), ('imaging', 'Imaging'), ('preventive', 'Preventive'), ('chronic_monitoring', 'Chronic Monitoring'), ('dental', 'Dental'), ('mental_health', 'Mental Health')], max_length=30)),
                ('description', models.TextField(blank=True)),
                ('criteria', models.JSONField(default=dict)),
                ('recommendation', models.TextField(blank=True)),
                ('frequency_days', models.PositiveIntegerField(blank=True, null=True)),
                ('applies_to_conditions', models.JSONField(default=list)),
                ('age_min', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('age_max', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('applies_to_gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('all', 'All')], default='all', max_length=10)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cymed_ph_gap_rules',
            },
        ),
        migrations.CreateModel(
            name='CareGapRecommendation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('recommendation_text', models.TextField()),
                ('recommended_by_provider_id', models.UUIDField(blank=True, null=True)),
                ('recommendation_date', models.DateField(auto_now_add=True)),
                ('target_date', models.DateField(blank=True, null=True)),
                ('loinc_code', models.CharField(blank=True, max_length=30)),
                ('service_type', models.CharField(blank=True, max_length=100)),
                ('is_ai_generated', models.BooleanField(default=False)),
                ('care_gap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to='cymed_ph_care_gaps.caregap')),
            ],
            options={
                'db_table': 'cymed_ph_gap_recommendations',
            },
        ),
        migrations.CreateModel(
            name='CareGapResolution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('resolved_by_user_id', models.UUIDField()),
                ('resolution_date', models.DateField()),
                ('resolution_type', models.CharField(choices=[('completed', 'Completed'), ('waived', 'Waived'), ('declined', 'Declined'), ('transferred', 'Transferred'), ('auto_closed', 'Auto Closed')], max_length=20)),
                ('resolution_notes', models.TextField(blank=True)),
                ('service_date', models.DateField(blank=True, null=True)),
                ('encounter_id', models.UUIDField(blank=True, null=True)),
                ('care_gap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resolutions', to='cymed_ph_care_gaps.caregap')),
            ],
            options={
                'db_table': 'cymed_ph_gap_resolutions',
            },
        ),
    ]
