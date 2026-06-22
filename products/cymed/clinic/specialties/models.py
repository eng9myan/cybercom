from django.db import models
from platform.common.models import BaseModel

class SpecialtyProfile(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_clinic_specialty_profiles"

    def __str__(self) -> str:
        return self.name

class SpecialtyTemplate(BaseModel):
    specialty = models.ForeignKey(SpecialtyProfile, on_delete=models.CASCADE, related_name="templates")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    schema_definition = models.JSONField(default=dict)  # JSON schema for form fields

    class Meta:
        db_table = "cymed_clinic_specialty_templates"
        unique_together = [("specialty", "code")]

class SpecialtyQuestionnaire(BaseModel):
    specialty = models.ForeignKey(SpecialtyProfile, on_delete=models.CASCADE, related_name="questionnaires")
    title = models.CharField(max_length=255)
    questions_json = models.JSONField(default=list)  # list of questions

    class Meta:
        db_table = "cymed_clinic_specialty_questionnaires"

class SpecialtyClinicalRule(BaseModel):
    specialty = models.ForeignKey(SpecialtyProfile, on_delete=models.CASCADE, related_name="clinical_rules")
    rule_name = models.CharField(max_length=255)
    trigger_expression = models.CharField(max_length=500)  # simple evaluation expression
    action_type = models.CharField(max_length=100)  # e.g., "alert", "recommendation"
    action_message = models.TextField()

    class Meta:
        db_table = "cymed_clinic_specialty_rules"
