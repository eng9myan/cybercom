"""
Pre-transmission rules, PDMP lookups and transmission.

Controlled-substance rules (applied before anything leaves the building):
  * the prescriber's controlled-substance registration (prescriber_dea) is
    required;
  * Schedule II prescriptions may not carry refills;
  * no Schedule I prescriptions at all;
  * when ``CYMED_PDMP_REQUIRED=1`` a PDMP check must exist for the
    prescription, and a ``review`` result must be attested by a prescriber.

PDMP lookups go to ``CYMED_PDMP_URL`` (FHIR search on MedicationDispense for
the patient); without it the check is recorded honestly as not_configured.
"""
from __future__ import annotations

import os

import httpx
from django.utils import timezone

from products.cymed.integrations.erx import transport
from products.cymed.integrations.erx.fhir import build_bundle
from products.cymed.integrations.erx.models import ErxTransmission, PdmpCheck

TRANSMITTABLE = {"active", "pending"}


def pdmp_required() -> bool:
    return os.environ.get("CYMED_PDMP_REQUIRED", "0") == "1"


def rule_violations(rx) -> list[str]:
    problems = []
    if rx.status not in TRANSMITTABLE:
        problems.append(f"Prescription is {rx.status}; only pending/active prescriptions can be sent.")
    if not rx.items.filter(is_active=True).exists():
        problems.append("Prescription has no active items.")
    if rx.is_controlled:
        if rx.dea_schedule == "I":
            problems.append("Schedule I substances cannot be prescribed.")
        if not rx.prescriber_dea:
            problems.append("Controlled prescription: prescriber's controlled-substance registration is missing.")
        if rx.dea_schedule == "II" and rx.refills_authorized:
            problems.append("Schedule II prescriptions cannot authorise refills.")
        if pdmp_required():
            check = rx.pdmp_checks.order_by("-created_at").first()
            if check is None or check.result in ("not_configured", "failed"):
                problems.append("A completed PDMP check is required before sending a controlled prescription.")
            elif check.result == "review" and not check.reviewed_at:
                problems.append("PDMP check flagged history: a prescriber must attest review first.")
    return problems


def run_pdmp_check(rx, *, checked_by: str) -> PdmpCheck:
    url = os.environ.get("CYMED_PDMP_URL", "").strip()
    base = dict(tenant_id=rx.tenant_id, prescription=rx, patient_id=rx.patient_id, checked_by=checked_by)
    if not url:
        return PdmpCheck.objects.create(result="not_configured", summary={
            "detail": "Set CYMED_PDMP_URL to query the prescription monitoring programme."}, **base)
    headers = {"Accept": "application/fhir+json"}
    token = os.environ.get("CYMED_PDMP_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = httpx.get(f"{url.rstrip('/')}/MedicationDispense",
                         params={"subject": f"Patient/{rx.patient_id}", "_count": 100},
                         headers=headers, timeout=15)
        resp.raise_for_status()
        bundle = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        return PdmpCheck.objects.create(result="failed", summary={"detail": exc.__class__.__name__}, **base)
    dispenses = [e.get("resource", {}) for e in bundle.get("entry", [])]
    controlled = [d for d in dispenses if "controlled" in str(d.get("category", "")).lower()]
    prescribers = {str(d.get("performer")) for d in controlled}
    # Flag for review on the classic warning signs: several controlled fills,
    # or controlled fills from more than one prescriber.
    result = "review" if len(controlled) >= 3 or len(prescribers) > 1 else "clear"
    return PdmpCheck.objects.create(result=result, summary={
        "dispenses": len(dispenses), "controlled_dispenses": len(controlled),
        "distinct_prescribers": len(prescribers)}, **base)


def transmit(rx, *, network: str, sent_by: str) -> ErxTransmission:
    attempt = rx.erx_transmissions.filter(network=network).count() + 1
    bundle = build_bundle(rx, network=network)
    common = dict(tenant_id=rx.tenant_id, prescription=rx, network=network, payload=bundle,
                  sent_by=sent_by, attempt=attempt)
    problems = rule_violations(rx)
    if problems:
        return ErxTransmission.objects.create(status="blocked", detail="\n".join(problems), **common)
    result = transport.send(network, bundle)
    tx = ErxTransmission.objects.create(status=result.status, detail=result.detail,
                                        response=result.response or {}, external_id=result.external_id,
                                        **common)
    if result.status in ("accepted", "sent") and rx.status == "pending":
        rx.status = "active"
        rx.save(update_fields=["status", "updated_at"])
    return tx


def attest_pdmp_review(check: PdmpCheck, *, reviewer: str) -> PdmpCheck:
    check.reviewed_by = reviewer
    check.reviewed_at = timezone.now()
    check.save(update_fields=["reviewed_by", "reviewed_at", "updated_at"])
    return check
