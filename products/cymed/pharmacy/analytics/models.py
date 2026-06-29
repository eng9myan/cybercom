"""
CyMed Pharmacy — Analytics & Dashboard Module
Pharmacy Operations Dashboard, Clinical Pharmacy Dashboard,
Medication Safety Dashboard, Executive Dashboard.

CyCom ERP owns actual inventory/finance data.
CyAI provides medication safety analytics and predictive insights.
This module provides pharmacy-domain aggregations and metrics.
"""

from django.db import models

from platform.common.models import BaseModel


class PharmacyDashboardSnapshot(BaseModel):
    """
    Point-in-time pharmacy operations snapshot.
    Pre-computed metrics for dashboard performance.
    """

    SNAPSHOT_TYPES = [
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    snapshot_type = models.CharField(max_length=20, choices=SNAPSHOT_TYPES, default="daily")
    snapshot_date = models.DateField(db_index=True)
    snapshot_hour = models.PositiveSmallIntegerField(null=True, blank=True)  # For hourly

    # Prescription metrics
    prescriptions_total = models.PositiveIntegerField(default=0)
    prescriptions_pending = models.PositiveIntegerField(default=0)
    prescriptions_dispensed = models.PositiveIntegerField(default=0)
    prescriptions_cancelled = models.PositiveIntegerField(default=0)
    controlled_substance_count = models.PositiveIntegerField(default=0)

    # Dispensing metrics
    dispense_orders_total = models.PositiveIntegerField(default=0)
    dispense_avg_minutes = models.FloatField(default=0.0)
    dispense_verified_count = models.PositiveIntegerField(default=0)
    dispense_errors = models.PositiveIntegerField(default=0)
    automation_dispense_count = models.PositiveIntegerField(default=0)

    # Clinical metrics
    drug_interactions_detected = models.PositiveIntegerField(default=0)
    interactions_overridden = models.PositiveIntegerField(default=0)
    clinical_interventions = models.PositiveIntegerField(default=0)
    recommendations_accepted = models.PositiveIntegerField(default=0)
    polypharmacy_cases = models.PositiveIntegerField(default=0)

    # Reconciliation
    reconciliations_completed = models.PositiveIntegerField(default=0)
    conflicts_identified = models.PositiveIntegerField(default=0)

    # Financial (reference to CyCom ERP — no duplication)
    total_medication_charges_ref = models.CharField(max_length=255, blank=True)  # ERP reference

    class Meta:
        db_table = "cymed_pharmacy_dashboard_snapshots"
        unique_together = [("tenant_id", "snapshot_type", "snapshot_date", "snapshot_hour")]
        indexes = [
            models.Index(fields=["tenant_id", "snapshot_type", "snapshot_date"]),
        ]


class MedicationSafetyEvent(BaseModel):
    """
    Medication safety event tracking (near-misses, errors, adverse events).
    Feeds into the Medication Safety Dashboard.
    """

    EVENT_TYPES = [
        ("near_miss", "Near Miss"),
        ("prescribing_error", "Prescribing Error"),
        ("transcription_error", "Transcription Error"),
        ("dispensing_error", "Dispensing Error"),
        ("administration_error", "Administration Error"),
        ("adverse_drug_event", "Adverse Drug Event"),
        ("adverse_drug_reaction", "Adverse Drug Reaction"),
    ]
    SEVERITY_CHOICES = [
        ("a", "Category A — No Error"),
        ("b", "Category B — Error / No Harm"),
        ("c", "Category C — Error / Monitoring"),
        ("d", "Category D — Error / Intervention"),
        ("e", "Category E — Error / Temporary Harm"),
        ("f", "Category F — Error / Prolonged Harm"),
        ("g", "Category G — Error / Permanent Harm"),
        ("h", "Category H — Error / Near Death"),
        ("i", "Category I — Error / Patient Death"),
    ]

    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=5, choices=SEVERITY_CHOICES, default="b")
    patient_id = models.UUIDField(null=True, blank=True, db_index=True)
    prescription_id = models.UUIDField(null=True, blank=True)
    dispense_order_id = models.UUIDField(null=True, blank=True)
    drug_code = models.CharField(max_length=100, blank=True)
    drug_name = models.CharField(max_length=500, blank=True)
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    contributing_factors = models.JSONField(default=list)
    corrective_action = models.TextField(blank=True)
    reported_by = models.UUIDField()
    occurred_at = models.DateTimeField()
    discovered_at = models.DateTimeField(auto_now_add=True)
    is_reported_to_authority = models.BooleanField(default=False)
    authority_report_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_medication_safety_events"
        indexes = [
            models.Index(fields=["tenant_id", "event_type", "severity"]),
            models.Index(fields=["patient_id", "occurred_at"]),
        ]


class PharmacyAnalyticsConfig(BaseModel):
    """Configuration for pharmacy analytics and dashboard settings."""

    dashboard_type = models.CharField(
        max_length=30,
        choices=[
            ("operations", "Pharmacy Operations"),
            ("clinical", "Clinical Pharmacy"),
            ("safety", "Medication Safety"),
            ("executive", "Executive"),
        ],
    )
    metrics_enabled = models.JSONField(default=list)
    alert_thresholds = models.JSONField(default=dict)
    refresh_interval_minutes = models.PositiveSmallIntegerField(default=15)
    email_recipients = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_pharmacy_analytics_config"
