import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approval_type', models.CharField(
                    choices=[
                        ('medication_approval', 'Medication Approval'),
                        ('controlled_substance', 'Controlled Substance'),
                        ('leave_request', 'Leave Request'),
                        ('schedule_change', 'Schedule Change'),
                        ('procedure_authorization', 'Procedure Authorization'),
                        ('referral', 'Referral'),
                        ('discharge_override', 'Discharge Override'),
                        ('administrative', 'Administrative'),
                        ('clinical_protocol_deviation', 'Clinical Protocol Deviation'),
                        ('research', 'Research'),
                    ],
                    max_length=30,
                )),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField()),
                ('requested_by_provider_id', models.UUIDField(db_index=True)),
                ('requested_by_name', models.CharField(max_length=255)),
                ('approver_id', models.UUIDField(db_index=True)),
                ('approver_name', models.CharField(max_length=255)),
                ('patient_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('reference_id', models.UUIDField(blank=True, null=True)),
                ('reference_type', models.CharField(blank=True, max_length=100)),
                ('priority', models.CharField(
                    choices=[('routine', 'Routine'), ('urgent', 'Urgent'), ('stat', 'STAT')],
                    default='routine',
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected'),
                        ('cancelled', 'Cancelled'),
                        ('expired', 'Expired'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('due_by', models.DateTimeField(blank=True, null=True)),
                ('decided_at', models.DateTimeField(blank=True, null=True)),
                ('approval_notes', models.TextField(blank=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('escalated_at', models.DateTimeField(blank=True, null=True)),
                ('escalated_to', models.UUIDField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_prov_approval_requests',
            },
        ),
        migrations.CreateModel(
            name='ApprovalWorkflow',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('workflow_name', models.CharField(max_length=255)),
                ('approval_type', models.CharField(max_length=30)),
                ('steps', models.JSONField(default=list)),
                ('is_sequential', models.BooleanField(default=True)),
                ('requires_all_approvers', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by_provider_id', models.UUIDField()),
                ('specialty', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'db_table': 'cymed_prov_approval_workflows',
            },
        ),
        migrations.CreateModel(
            name='ApprovalDecision',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approval_request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='decisions',
                    to='cymed_provider_approvals.approvalrequest',
                )),
                ('decided_by_provider_id', models.UUIDField()),
                ('decided_by_name', models.CharField(max_length=255)),
                ('decision', models.CharField(
                    choices=[
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected'),
                        ('requested_more_info', 'Requested More Info'),
                        ('delegated', 'Delegated'),
                    ],
                    max_length=25,
                )),
                ('decision_notes', models.TextField(blank=True)),
                ('conditions', models.TextField(blank=True)),
                ('delegated_to', models.UUIDField(blank=True, null=True)),
                ('step_order', models.PositiveSmallIntegerField(default=1)),
            ],
            options={
                'db_table': 'cymed_prov_approval_decisions',
            },
        ),
        migrations.CreateModel(
            name='ApprovalAuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approval_request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='audit_log',
                    to='cymed_provider_approvals.approvalrequest',
                )),
                ('action', models.CharField(
                    choices=[
                        ('created', 'Created'),
                        ('submitted', 'Submitted'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected'),
                        ('cancelled', 'Cancelled'),
                        ('escalated', 'Escalated'),
                        ('delegated', 'Delegated'),
                        ('expired', 'Expired'),
                        ('viewed', 'Viewed'),
                    ],
                    max_length=20,
                )),
                ('performed_by_provider_id', models.UUIDField()),
                ('performed_by_name', models.CharField(max_length=255)),
                ('details', models.JSONField(default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_prov_approval_audit',
            },
        ),
        migrations.AddIndex(
            model_name='approvalrequest',
            index=models.Index(
                fields=['tenant_id', 'approver_id', 'status'],
                name='cymed_prov_ar_tenant_approver_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='approvalrequest',
            index=models.Index(
                fields=['tenant_id', 'requested_by_provider_id', 'status'],
                name='cymed_prov_ar_tenant_requester_status_idx',
            ),
        ),
    ]
