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
            name='QualityMeasure',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('measure_code', models.CharField(max_length=50, unique=True)),
                ('measure_name', models.CharField(max_length=200)),
                ('measure_type', models.CharField(choices=[('process', 'Process'), ('outcome', 'Outcome'), ('structure', 'Structure'), ('composite', 'Composite'), ('patient_reported', 'Patient Reported')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('numerator_definition', models.JSONField(default=dict)),
                ('denominator_definition', models.JSONField(default=dict)),
                ('target_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('benchmark_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('is_national', models.BooleanField(default=False)),
                ('reporting_period', models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')], default='annual', max_length=20)),
                ('related_icd11_codes', models.JSONField(default=list)),
                ('loinc_codes', models.JSONField(default=list)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cymed_ph_qual_measures',
            },
        ),
        migrations.CreateModel(
            name='QualityMeasureResult',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('facility_id', models.UUIDField(db_index=True)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('numerator', models.PositiveIntegerField(default=0)),
                ('denominator', models.PositiveIntegerField(default=0)),
                ('performance_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('benchmark_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('meets_target', models.BooleanField(default=False)),
                ('calculated_at', models.DateTimeField(auto_now_add=True)),
                ('measure', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='results', to='cymed_ph_quality.qualitymeasure')),
            ],
            options={
                'db_table': 'cymed_ph_qual_results',
                'unique_together': {('tenant_id', 'measure', 'facility_id', 'period_start', 'period_end')},
            },
        ),
        migrations.CreateModel(
            name='QualityImprovement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('intervention_type', models.CharField(choices=[('process_change', 'Process Change'), ('training', 'Training'), ('technology', 'Technology'), ('policy', 'Policy'), ('care_pathway', 'Care Pathway'), ('audit_feedback', 'Audit and Feedback'), ('other', 'Other')], max_length=50)),
                ('intervention_description', models.TextField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('active', 'Active'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='planned', max_length=20)),
                ('expected_improvement', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('actual_improvement', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('responsible_user_id', models.UUIDField(blank=True, null=True)),
                ('measure_result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='improvements', to='cymed_ph_quality.qualitymeasureresult')),
            ],
            options={
                'db_table': 'cymed_ph_qual_improvements',
            },
        ),
        migrations.CreateModel(
            name='ClinicalAudit',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('tenant_id', models.UUIDField(db_index=True, editable=False)),
                ('audit_name', models.CharField(max_length=200)),
                ('audit_type', models.CharField(choices=[('clinical_practice', 'Clinical Practice'), ('medication', 'Medication'), ('infection_control', 'Infection Control'), ('documentation', 'Documentation'), ('patient_safety', 'Patient Safety'), ('outcome', 'Outcome'), ('process', 'Process')], max_length=30)),
                ('facility_id', models.UUIDField(db_index=True)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('audit_criteria', models.JSONField(default=list)),
                ('auditor_id', models.UUIDField()),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('reported', 'Reported')], default='planned', max_length=20)),
                ('sample_size', models.PositiveIntegerField(default=0)),
                ('compliant_count', models.PositiveIntegerField(default=0)),
                ('compliance_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('findings', models.JSONField(default=list)),
                ('recommendations', models.JSONField(default=list)),
            ],
            options={
                'db_table': 'cymed_ph_qual_audits',
            },
        ),
    ]
