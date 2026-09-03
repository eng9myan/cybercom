"""High-level RCM services orchestrating engines + models + payer clients."""
from __future__ import annotations

from decimal import Decimal

from django.apps import apps
from django.utils import timezone

from .engines import (
    AppealComposer,
    AutoCodingEngine,
    ClaimScrubber,
    DenialPredictor,
    PayerRuleEngine,
    PreAuthOrchestrator,
)
from .models import AppealCase, Claim837, ClaimResponse


def build_claim_from_bill(*, bill_id, encounter_id, payer_code: str,
                           payer_country: str = "SA",
                           kind: str = "professional") -> Claim837:
    Bill = apps.get_model("cymed_payments", "UnifiedBill")
    bill = Bill.objects.get(id=bill_id)

    # Auto-code
    coder = AutoCodingEngine()
    clinical_text = ""  # would fetch from encounter notes
    proc_text = " ".join(li.service_name for li in bill.line_items.all())
    coded = coder.code_encounter(encounter_id=str(encounter_id),
                                   clinical_text=clinical_text,
                                   procedures_text=proc_text)

    claim = Claim837.objects.create(
        bill_id=bill.id,
        encounter_id=encounter_id,
        patient_profile_id=bill.patient_profile_id,
        kind=kind,
        payer_code=payer_code.upper(),
        payer_country=payer_country.upper(),
        diagnosis_codes=[{"icd11": s["icd11"], "label": s.get("label"), "primary": i == 0}
                          for i, s in enumerate(coded.get("icd11_suggestions", []))],
        procedure_codes=[{"cpt": c["cpt"], "modifier": "", "qty": 1,
                           "matched": c.get("matched")}
                          for c in coded.get("cpt_suggestions", [])],
        charge_total=bill.total,
    )
    return claim


def scrub_and_predict(*, claim_id) -> dict:
    claim = Claim837.objects.get(id=claim_id)
    errors = ClaimScrubber().scrub(claim)
    errors += PayerRuleEngine().check(claim)
    prediction = DenialPredictor().predict(claim, scrub_errors=errors)
    claim.scrub_errors = errors
    claim.denial_risk = Decimal(str(prediction["risk"]))
    claim.denial_risk_drivers = prediction["drivers"]
    claim.status = "scrubbed"
    claim.save(update_fields=["scrub_errors", "denial_risk",
                                "denial_risk_drivers", "status", "updated_at"])
    return {"errors": errors, "prediction": prediction}


def submit_claim(*, claim_id) -> ClaimResponse | dict:
    claim = Claim837.objects.get(id=claim_id)
    if claim.status not in ("scrubbed", "draft"):
        return {"error": f"cannot submit from status {claim.status}"}

    # Route to insurer via payments insurer registry
    try:
        from products.cymed.payments.insurers import get_insurer
    except ImportError:
        return {"error": "payments insurer registry unavailable"}
    insurer = get_insurer(claim.payer_code, claim.payer_country)

    bill = apps.get_model("cymed_payments", "UnifiedBill").objects.get(id=claim.bill_id)
    result = insurer.claim_submit(bill)

    claim.submitted_at = timezone.now()
    claim.external_reference = result.reference_number or ""
    claim.status = "submitted" if result.accepted else "rejected"
    claim.save(update_fields=["submitted_at", "external_reference", "status", "updated_at"])

    return ClaimResponse.objects.create(
        claim=claim,
        outcome="accepted" if result.accepted else "rejected",
        payer_reference=result.reference_number,
        denial_codes=([{"note": result.denial_reason}] if result.denial_reason else []),
        remittance_advice_raw=result.raw,
    )


def raise_appeal(*, claim_id, narrative: str,
                  denial_codes: list[dict] | None = None,
                  level: int = 1) -> AppealCase:
    claim = Claim837.objects.get(id=claim_id)
    denial_codes = denial_codes or []
    if not denial_codes:
        # Aggregate from latest ClaimResponse
        last = claim.responses.order_by("-created_at").first()
        if last:
            denial_codes = last.denial_codes or []
    composer = AppealComposer()
    letter = composer.compose(claim=claim, denial_codes=denial_codes,
                                narrative=narrative)
    return AppealCase.objects.create(
        claim=claim, level=level,
        denial_codes_addressed=denial_codes,
        appeal_letter_html=letter,
    )


def kpi_snapshot() -> dict:
    """Denial rate, DSO, first-pass yield, AR aging — network-wide."""
    from django.db.models import Avg, Count, Q, Sum

    total = Claim837.objects.count()
    denied = Claim837.objects.filter(status__in=["denied", "rejected"]).count()
    paid = Claim837.objects.filter(status="paid").count()
    submitted = Claim837.objects.filter(status__in=["submitted", "accepted", "paid",
                                                      "denied", "appealed"]).count()
    denial_rate = (denied / submitted) if submitted else 0
    first_pass = (paid / submitted) if submitted else 0
    dso_avg = Claim837.objects.filter(dso_days__isnull=False).aggregate(Avg("dso_days"))["dso_days__avg"] or 0

    ar_total = (Claim837.objects
                .filter(status__in=["submitted", "accepted", "denied"])
                .aggregate(Sum("charge_total"))["charge_total__sum"]) or 0

    return {
        "total_claims": total,
        "denial_rate": round(denial_rate, 3),
        "first_pass_yield": round(first_pass, 3),
        "average_dso_days": round(float(dso_avg), 1),
        "ar_outstanding": str(ar_total),
    }
