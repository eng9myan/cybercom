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
            name='RiskCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('category_code', models.CharField(max_length=50, unique=True)),
                ('category_name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('low_threshold', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('moderate_threshold', models.DecimalField(decimal_places=2, default=30, max_digits=5)),
                ('high_threshold', models.DecimalField(decimal_places=2, default=60, max_digits=5)),
                ('very_high_threshold', models.DecimalField(decimal_places=2, default=80, max_digits=5)),
                ('interventions', models.JSONField(default=list)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cymed_ph_risk_categories',
            },
        ),
        migrations.CreateModel(
            name='RiskScore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('risk_category', models.CharField(choices=[('readmission', 'Readmission'), ('mortality', 'Mortality'), ('chronic_disease', 'Chronic Disease'), ('high_cost', 'High Cost'), ('preventable_ed', 'Preventable ED'), ('falls', 'Falls'), ('mental_health', 'Mental Health'), ('sepsis', 'Sepsis'), ('malnutrition', 'Malnutrition')], max_length=30)),
                ('score', models.DecimalField(decimal_places=2, max_digits=5)),
                ('risk_level', models.CharField(choices=[('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High'), ('very_high', 'Very High'), ('critical', 'Critical')], max_length=15)),
                ('score_date', models.DateField()),
                ('model_version', models.CharField(blank=True, max_length=50)),
                ('is_ai_generated', models.BooleanField(default=False)),
                ('is_advisory_only', models.BooleanField(default=True, editable=False)),
                ('contributing_factors', models.JSONField(default=list)),
                ('valid_until', models.DateField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_ph_risk_scores',
                'ordering': ['-score_date'],
            },
        ),
        migrations.CreateModel(
            name='RiskFactor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('factor_name', models.CharField(max_length=200)),
                ('factor_type', models.CharField(choices=[('clinical', 'Clinical'), ('demographic', 'Demographic'), ('behavioral', 'Behavioral'), ('social', 'Social'), ('historical', 'Historical')], max_length=30)),
                ('factor_value', models.CharField(blank=True, max_length=200)),
                ('contribution_weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('icd11_code', models.CharField(blank=True, max_length=20)),
                ('risk_score', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='factors', to='cymed_ph_risk_management.riskscore')),
            ],
            options={
                'db_table': 'cymed_ph_risk_factors',
            },
        ),
        migrations.CreateModel(
            name='RiskAssessment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('assessment_type', models.CharField(choices=[('automated', 'Automated'), ('manual', 'Manual'), ('combined', 'Combined')], default='automated', max_length=20)),
                ('assessment_date', models.DateField()),
                ('overall_risk_level', models.CharField(choices=[('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High'), ('very_high', 'Very High'), ('critical', 'Critical')], max_length=15)),
                ('overall_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('assessor_user_id', models.UUIDField(blank=True, null=True)),
                ('recommendations', models.JSONField(default=list)),
                ('next_assessment_date', models.DateField(blank=True, null=True)),
                ('is_ai_generated', models.BooleanField(default=False)),
                ('is_advisory_only', models.BooleanField(default=True, editable=False)),
                ('status', models.CharField(choices=[('pending_review', 'Pending Review'), ('acknowledged', 'Acknowledged'), ('acted_upon', 'Acted Upon'), ('archived', 'Archived')], default='pending_review', max_length=20)),
                ('acknowledged_by_user_id', models.UUIDField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_ph_risk_assessments',
            },
        ),
    ]
