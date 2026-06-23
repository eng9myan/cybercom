import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='FamilyGroup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner_account_id', models.UUIDField(db_index=True)),
                ('group_name', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'cymed_portal_family_groups',
            },
        ),
        migrations.CreateModel(
            name='FamilyMember',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='members',
                    to='cymed_portal_family_accounts.familygroup',
                )),
                ('member_account_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('relationship', models.CharField(
                    choices=[
                        ('spouse', 'Spouse'),
                        ('child', 'Child'),
                        ('parent', 'Parent'),
                        ('sibling', 'Sibling'),
                        ('guardian', 'Guardian'),
                        ('dependent', 'Dependent'),
                        ('other', 'Other'),
                    ],
                    max_length=50,
                )),
                ('is_minor', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('added_by', models.UUIDField()),
            ],
            options={
                'db_table': 'cymed_portal_family_members',
            },
        ),
        migrations.AddIndex(
            model_name='familymember',
            index=models.Index(fields=['group', 'patient_id'], name='cymed_portal_fam_grp_pat_idx'),
        ),
        migrations.CreateModel(
            name='FamilyAccessPermission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('grantor_account_id', models.UUIDField(db_index=True)),
                ('grantee_account_id', models.UUIDField(db_index=True)),
                ('patient_id', models.UUIDField(db_index=True)),
                ('access_level', models.CharField(
                    choices=[
                        ('view_only', 'View Only'),
                        ('full_access', 'Full Access'),
                        ('emergency_only', 'Emergency Only'),
                        ('appointments_only', 'Appointments Only'),
                    ],
                    max_length=30,
                )),
                ('permissions', models.JSONField(default=list)),
                ('valid_from', models.DateField(blank=True, null=True)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('revoked_at', models.DateTimeField(blank=True, null=True)),
                ('revoked_by', models.UUIDField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_portal_family_access',
            },
        ),
        migrations.AddIndex(
            model_name='familyaccesspermission',
            index=models.Index(
                fields=['grantor_account_id', 'grantee_account_id', 'is_active'],
                name='cymed_portal_fam_acc_grant_idx',
            ),
        ),
        migrations.CreateModel(
            name='DependentProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('member', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='dependent_profile',
                    to='cymed_portal_family_accounts.familymember',
                )),
                ('guardian_account_id', models.UUIDField(db_index=True)),
                ('school_name', models.CharField(blank=True, max_length=255)),
                ('pediatric_notes', models.TextField(blank=True)),
                ('allergies_summary', models.TextField(blank=True)),
                ('immunization_up_to_date', models.BooleanField(default=False)),
                ('next_checkup_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'db_table': 'cymed_portal_dependent_profiles',
            },
        ),
    ]
