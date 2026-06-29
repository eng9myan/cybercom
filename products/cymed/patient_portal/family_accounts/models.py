from django.db import models

from platform.common.models import BaseModel


class FamilyGroup(BaseModel):
    owner_account_id = models.UUIDField(db_index=True)
    group_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_portal_family_groups"

    def __str__(self):
        return f"{self.group_name or 'Family Group'} (owner: {self.owner_account_id})"


class FamilyMember(BaseModel):
    RELATIONSHIP_CHOICES = [
        ("spouse", "Spouse"),
        ("child", "Child"),
        ("parent", "Parent"),
        ("sibling", "Sibling"),
        ("guardian", "Guardian"),
        ("dependent", "Dependent"),
        ("other", "Other"),
    ]

    group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        related_name="members",
    )
    member_account_id = models.UUIDField(null=True, blank=True, db_index=True)
    patient_id = models.UUIDField(db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    relationship = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)
    is_minor = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    added_by = models.UUIDField()

    class Meta:
        db_table = "cymed_portal_family_members"
        indexes = [
            models.Index(fields=["group", "patient_id"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.relationship})"


class FamilyAccessPermission(BaseModel):
    ACCESS_LEVEL_CHOICES = [
        ("view_only", "View Only"),
        ("full_access", "Full Access"),
        ("emergency_only", "Emergency Only"),
        ("appointments_only", "Appointments Only"),
    ]

    grantor_account_id = models.UUIDField(db_index=True)
    grantee_account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    access_level = models.CharField(max_length=30, choices=ACCESS_LEVEL_CHOICES)
    permissions = models.JSONField(default=list)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_portal_family_access"
        indexes = [
            models.Index(fields=["grantor_account_id", "grantee_account_id", "is_active"]),
        ]

    def __str__(self):
        return (
            f"Access: {self.grantee_account_id} -> patient {self.patient_id} ({self.access_level})"
        )


class DependentProfile(BaseModel):
    member = models.OneToOneField(
        FamilyMember,
        on_delete=models.CASCADE,
        related_name="dependent_profile",
    )
    guardian_account_id = models.UUIDField(db_index=True)
    school_name = models.CharField(max_length=255, blank=True)
    pediatric_notes = models.TextField(blank=True)
    allergies_summary = models.TextField(blank=True)
    immunization_up_to_date = models.BooleanField(default=False)
    next_checkup_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_portal_dependent_profiles"

    def __str__(self):
        return f"Dependent profile for {self.member.first_name} {self.member.last_name}"
