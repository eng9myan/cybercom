"""RCM data model — claims, responses, denials, appeals, caches."""
import secrets
from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel, SoftDeleteMixin


def _default_claim_number():
    return f"CLM-{secrets.token_hex(6).upper()}"


class Claim837(BaseModel, SoftDeleteMixin):
    KIND = [("professional", "837P Professional"), ("institutional", "837I Institutional")]
    STATUS = [("draft", "Draft"), ("scrubbed", "Scrubbed"),
              ("submitted", "Submitted"), ("accepted", "Accepted"),
              ("rejected", "Rejected"), ("paid", "Paid"),
              ("denied", "Denied"), ("appealed", "Appealed")]

    claim_number = models.CharField(max_length=50, unique=True, default=_default_claim_number)
    bill_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    kind = models.CharField(max_length=20, choices=KIND, default="professional")
    payer_code = models.CharField(max_length=50, db_index=True)
    payer_country = models.CharField(max_length=2, default="SA")

    diagnosis_codes = models.JSONField(default=list)      # [{icd11, primary}]
    procedure_codes = models.JSONField(default=list)      # [{cpt, modifier, qty}]
    charge_total = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))

    status = models.CharField(max_length=20, choices=STATUS, default="draft", db_index=True)
    scrub_errors = models.JSONField(default=list, blank=True)
    denial_risk = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
    denial_risk_drivers = models.JSONField(default=list, blank=True)

    x12_payload = models.TextField(blank=True)            # generated 837 EDI
    fhir_payload = models.JSONField(default=dict, blank=True)  # NPHIES bundle
    external_reference = models.CharField(max_length=200, blank=True)  # payer's ID
    submitted_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    denied_at = models.DateTimeField(null=True, blank=True)
    dso_days = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cymed_rcm_claims"
        ordering = ["-created_at"]


class ClaimResponse(BaseModel):
    """Payer response — one row per response event (may be many per claim)."""
    OUTCOME = [("accepted", "Accepted"), ("partial", "Partial"),
               ("rejected", "Rejected"), ("denied", "Denied"),
               ("paid", "Paid")]

    claim = models.ForeignKey(Claim837, on_delete=models.CASCADE, related_name="responses")
    outcome = models.CharField(max_length=20, choices=OUTCOME)
    payer_reference = models.CharField(max_length=200, blank=True)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    adjustments = models.JSONField(default=list, blank=True)   # [{code, amount, reason}]
    denial_codes = models.JSONField(default=list, blank=True)  # [{carc, rarc, note}]
    remittance_advice_raw = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_rcm_claim_responses"
        ordering = ["-created_at"]


class DenialCode(BaseModel):
    """CARC (Claim Adjustment Reason Codes) + RARC (Remittance Advice Remark Codes)."""
    TYPE = [("carc", "CARC"), ("rarc", "RARC"), ("local", "Payer-specific")]

    code_type = models.CharField(max_length=10, choices=TYPE)
    code = models.CharField(max_length=20, db_index=True)
    description = models.TextField()
    is_appealable = models.BooleanField(default=True)
    default_appeal_strategy = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "cymed_rcm_denial_codes"
        unique_together = [("code_type", "code")]


class AppealCase(BaseModel):
    STATUS = [("draft", "Draft"), ("submitted", "Submitted"),
              ("won", "Won"), ("lost", "Lost"), ("withdrawn", "Withdrawn")]
    LEVEL = [(1, "First-level"), (2, "Second-level"), (3, "External review")]

    claim = models.ForeignKey(Claim837, on_delete=models.CASCADE, related_name="appeals")
    level = models.IntegerField(choices=LEVEL, default=1)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    denial_codes_addressed = models.JSONField(default=list)
    appeal_letter_html = models.TextField(blank=True)
    supporting_docs = models.JSONField(default=list, blank=True)  # [{name, url}]
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    recovered_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "cymed_rcm_appeals"


class EligibilityCache(BaseModel):
    """24-h TTL cache on eligibility checks — avoid repeated NPHIES calls."""
    policy_id = models.UUIDField(db_index=True)
    service_code = models.CharField(max_length=50, db_index=True)
    covered = models.BooleanField()
    co_pay_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    requires_preauth = models.BooleanField(default=False)
    expires_at = models.DateTimeField(db_index=True)
    raw = models.JSONField(default=dict)

    class Meta:
        db_table = "cymed_rcm_eligibility_cache"
        indexes = [models.Index(fields=["policy_id", "service_code", "expires_at"])]
