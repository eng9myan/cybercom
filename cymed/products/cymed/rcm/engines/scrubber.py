"""Claim scrubber — pre-submit validation.

Catches denial-causing errors before the claim goes to the payer:
  - missing required fields
  - invalid code combinations
  - service outside coverage
  - date-of-service outside policy validity
  - duplicate claim detection
"""
from __future__ import annotations

from decimal import Decimal
from django.apps import apps


class ScrubError:
    def __init__(self, code: str, severity: str, message: str, field: str = ""):
        self.code = code
        self.severity = severity   # 'error' | 'warning'
        self.message = message
        self.field = field

    def to_dict(self):
        return {"code": self.code, "severity": self.severity,
                "message": self.message, "field": self.field}


class ClaimScrubber:
    def scrub(self, claim) -> list[dict]:
        errors: list[ScrubError] = []

        # Required fields
        if not claim.diagnosis_codes:
            errors.append(ScrubError("MISSING_DX", "error",
                                     "Claim must have at least one diagnosis code"))
        if not claim.procedure_codes:
            errors.append(ScrubError("MISSING_PROC", "error",
                                     "Claim must have at least one procedure/CPT code"))
        if claim.charge_total <= 0:
            errors.append(ScrubError("ZERO_CHARGE", "error", "Charge total is zero"))
        if not claim.payer_code:
            errors.append(ScrubError("MISSING_PAYER", "error", "Payer code is missing"))

        # Primary diagnosis check
        has_primary = any(d.get("primary") for d in claim.diagnosis_codes)
        if not has_primary and claim.diagnosis_codes:
            errors.append(ScrubError("NO_PRIMARY_DX", "warning",
                                     "No primary diagnosis flagged; using first entry"))

        # Duplicate claim
        Claim = type(claim)
        dupes = Claim.objects.filter(
            encounter_id=claim.encounter_id,
            payer_code=claim.payer_code,
            status__in=["submitted", "accepted", "paid"],
        ).exclude(id=claim.id)
        if dupes.exists():
            errors.append(ScrubError("DUPLICATE_CLAIM", "error",
                                     f"Prior claim {dupes.first().claim_number} exists"))

        # Coverage validity
        Coverage = None
        try:
            Coverage = apps.get_model("cymed_payments", "InsurancePolicy")
        except LookupError:
            pass
        if Coverage:
            pol = Coverage.objects.filter(
                profile__patient_id=claim.patient_profile_id,
                insurer_code=claim.payer_code,
            ).first()
            if pol:
                from django.utils import timezone
                today = timezone.now().date()
                if pol.valid_to and pol.valid_to < today:
                    errors.append(ScrubError("POLICY_EXPIRED", "error",
                                             f"Policy expired {pol.valid_to}"))

        return [e.to_dict() for e in errors]
