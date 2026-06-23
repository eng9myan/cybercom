import uuid
from django.db import models
from platform.common.models import BaseModel


class CareTeam(BaseModel):
    TEAM_TYPE_CHOICES = [
        ('primary', 'Primary'),
        ('specialty', 'Specialty'),
        ('multidisciplinary', 'Multidisciplinary'),
        ('on_call', 'On Call'),
        ('rapid_response', 'Rapid Response'),
        ('perioperative', 'Perioperative'),
        ('maternity', 'Maternity'),
        ('oncology', 'Oncology'),
        ('custom', 'Custom'),
    ]

    team_name = models.CharField(max_length=255)
    team_type = models.CharField(max_length=20, choices=TEAM_TYPE_CHOICES)
    patient_id = models.UUIDField(db_index=True, null=True, blank=True)
    unit_id = models.UUIDField(null=True, blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_by_provider_id = models.UUIDField()
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'cymed_prov_care_teams'

    def __str__(self):
        return f"{self.team_name} ({self.team_type})"


class CareTeamMember(BaseModel):
    ROLE_CHOICES = [
        ('attending', 'Attending'),
        ('resident', 'Resident'),
        ('intern', 'Intern'),
        ('charge_nurse', 'Charge Nurse'),
        ('nurse', 'Nurse'),
        ('pharmacist', 'Pharmacist'),
        ('therapist', 'Therapist'),
        ('social_worker', 'Social Worker'),
        ('care_coordinator', 'Care Coordinator'),
        ('consultant', 'Consultant'),
        ('student', 'Student'),
        ('other', 'Other'),
    ]

    care_team = models.ForeignKey(
        CareTeam,
        on_delete=models.CASCADE,
        related_name='members',
    )
    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    added_by = models.UUIDField()

    class Meta:
        db_table = 'cymed_prov_care_team_members'
        unique_together = [('tenant_id', 'care_team', 'provider_id')]

    def __str__(self):
        return f"{self.provider_name} ({self.role}) in team {self.care_team_id}"


class CareTeamAssignment(BaseModel):
    care_team = models.ForeignKey(
        CareTeam,
        on_delete=models.CASCADE,
        related_name='patient_assignments',
    )
    patient_id = models.UUIDField(db_index=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    unassigned_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    assignment_reason = models.TextField(blank=True)
    assigned_by = models.UUIDField()

    class Meta:
        db_table = 'cymed_prov_care_team_assignments'

    def __str__(self):
        return f"Patient {self.patient_id} assigned to team {self.care_team_id}"


class CareTeamRole(BaseModel):
    ROLE_TYPE_CHOICES = [
        ('physician', 'Physician'),
        ('nursing', 'Nursing'),
        ('pharmacy', 'Pharmacy'),
        ('allied_health', 'Allied Health'),
        ('administrative', 'Administrative'),
        ('other', 'Other'),
    ]

    role_code = models.CharField(max_length=50, unique=True)
    role_name = models.CharField(max_length=255)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPE_CHOICES)
    responsibilities = models.JSONField(default=list)
    can_order = models.BooleanField(default=False)
    can_sign_documents = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'cymed_prov_care_team_roles'

    def __str__(self):
        return f"{self.role_name} ({self.role_code})"


class CoverageSchedule(BaseModel):
    COVERAGE_TYPE_CHOICES = [
        ('on_call', 'On Call'),
        ('cross_cover', 'Cross Cover'),
        ('holiday', 'Holiday'),
        ('leave_cover', 'Leave Cover'),
    ]

    care_team = models.ForeignKey(
        CareTeam,
        on_delete=models.CASCADE,
        related_name='coverage_schedules',
    )
    covering_provider_id = models.UUIDField(db_index=True)
    covering_provider_name = models.CharField(max_length=255)
    covered_provider_id = models.UUIDField()
    coverage_date = models.DateField(db_index=True)
    coverage_start = models.TimeField()
    coverage_end = models.TimeField()
    coverage_type = models.CharField(max_length=20, choices=COVERAGE_TYPE_CHOICES, default='on_call')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'cymed_prov_coverage_schedules'

    def __str__(self):
        return f"{self.covering_provider_name} covering on {self.coverage_date} ({self.coverage_type})"
