"""
Electronic prescription transmission + controlled-substance monitoring checks.

An ErxTransmission is one attempt to send a Prescription to a national /
commercial e-prescribing network. Its status only ever reflects what the
network answered: a network that is not configured yields ``not_configured``,
never a fake ``sent``.

A PdmpCheck records a prescription-drug-monitoring lookup made before a
controlled prescription is transmitted.
"""
from django.db import models

from platform.common.models import BaseModel

NETWORKS = [
    ("nphies", "NPHIES (Saudi Arabia)"),
    ("wasfaty", "Wasfaty (Saudi Arabia)"),
    ("hakeem", "Hakeem (Jordan)"),
    ("fhir", "Generic FHIR R4 endpoint"),
]


class ErxTransmission(BaseModel):
    STATUS = [
        ("blocked", "Blocked by a pre-transmission rule"),
        ("not_configured", "Network not configured"),
        ("sent", "Sent, awaiting answer"),
        ("accepted", "Accepted by network"),
        ("rejected", "Rejected by network"),
        ("failed", "Transport failure"),
        ("cancelled", "Cancelled"),
    ]

    prescription = models.ForeignKey(
        "cymed_pharmacy_prescriptions.Prescription", on_delete=models.PROTECT, related_name="erx_transmissions"
    )
    network = models.CharField(max_length=20, choices=NETWORKS)
    status = models.CharField(max_length=20, choices=STATUS, db_index=True)
    detail = models.TextField(blank=True)  # human-readable reason for the status
    payload = models.JSONField(default=dict)  # FHIR Bundle that was (or would be) sent
    response = models.JSONField(default=dict, blank=True)
    external_id = models.CharField(max_length=200, blank=True, db_index=True)
    sent_by = models.CharField(max_length=255, blank=True)
    attempt = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "cymed_erx_transmissions"
        ordering = ["-created_at"]


class PdmpCheck(BaseModel):
    RESULTS = [
        ("clear", "No concerning history"),
        ("review", "History needs prescriber review"),
        ("not_configured", "PDMP not configured"),
        ("failed", "Lookup failed"),
    ]

    prescription = models.ForeignKey(
        "cymed_pharmacy_prescriptions.Prescription", on_delete=models.CASCADE, related_name="pdmp_checks"
    )
    patient_id = models.UUIDField(db_index=True)
    result = models.CharField(max_length=20, choices=RESULTS)
    summary = models.JSONField(default=dict, blank=True)
    # Prescriber attests they reviewed a "review" result before proceeding.
    reviewed_by = models.CharField(max_length=255, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    checked_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_erx_pdmp_checks"
        ordering = ["-created_at"]
