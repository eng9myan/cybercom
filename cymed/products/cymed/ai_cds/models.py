"""Persistent AI CDS artefacts — alerts, scoring history, feedback."""
from django.db import models

from platform.common.models import BaseModel


class CDSAlert(BaseModel):
    KIND = [
        ("drug_interaction", "Drug interaction"),
        ("drug_allergy", "Drug allergy"),
        ("dose_warning", "Dose warning"),
        ("renal_adjustment", "Renal dose adjustment"),
        ("pregnancy_contraindication", "Pregnancy contraindication"),
        ("pediatric_dose", "Pediatric dose check"),
        ("duplicate_therapy", "Duplicate therapy"),
        ("sepsis_early_warning", "Sepsis early warning"),
        ("readmission_risk", "Readmission risk"),
        ("fall_risk", "Fall risk"),
        ("deterioration", "Deterioration risk"),
    ]
    SEVERITY = [("info", "Info"), ("low", "Low"), ("medium", "Medium"),
                 ("high", "High"), ("critical", "Critical")]

    patient_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(db_index=True, null=True, blank=True)
    kind = models.CharField(max_length=40, choices=KIND, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY, db_index=True)
    title = models.CharField(max_length=200)
    detail = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)     # raw model output
    score = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    acknowledged_by = models.UUIDField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    overridden = models.BooleanField(default=False)
    override_reason = models.CharField(max_length=400, blank=True)

    class Meta:
        db_table = "cymed_cds_alerts"
        ordering = ["-created_at"]


class RiskScore(BaseModel):
    SCORE_TYPE = [
        ("sepsis", "Sepsis (qSOFA / SIRS)"),
        ("news2", "NEWS2 (National Early Warning Score)"),
        ("mews", "MEWS"),
        ("readmission_30d", "30-day readmission"),
        ("mortality_hospital", "In-hospital mortality"),
        ("fall_morse", "Fall risk (Morse)"),
        ("braden", "Braden pressure injury"),
    ]

    patient_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(db_index=True, null=True, blank=True)
    score_type = models.CharField(max_length=40, choices=SCORE_TYPE, db_index=True)
    value = models.DecimalField(max_digits=8, decimal_places=3)
    band = models.CharField(max_length=20, blank=True)       # 'low'|'moderate'|'high'|...
    features = models.JSONField(default=dict, blank=True)
    model_version = models.CharField(max_length=50, default="v1")

    class Meta:
        db_table = "cymed_cds_risk_scores"
        ordering = ["-created_at"]


class ICDCodeSuggestion(BaseModel):
    encounter_id = models.UUIDField(db_index=True)
    source_text = models.TextField()
    suggestions = models.JSONField(default=list)             # [{icd11, label, confidence}]
    accepted_code = models.CharField(max_length=20, blank=True)
    accepted_by = models.UUIDField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    model_version = models.CharField(max_length=50, default="cymed-icd11-nlp-v1")

    class Meta:
        db_table = "cymed_cds_icd_suggestions"
        ordering = ["-created_at"]
