"""Prescription → FHIR R4 message Bundle (one MedicationRequest per active item)."""
from __future__ import annotations

import uuid

from django.utils import timezone

_RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"


def _medication_request(rx, item, patient_ref: str, practitioner_ref: str) -> dict:
    req = {
        "resourceType": "MedicationRequest",
        "id": str(item.id),
        "identifier": [{"system": "urn:cymed:prescription", "value": rx.prescription_number}],
        "status": "active",
        "intent": "order",
        "priority": rx.priority if rx.priority in ("routine", "urgent", "stat") else "routine",
        "medicationCodeableConcept": {
            "coding": [{"system": _RXNORM, "code": item.drug_code, "display": item.drug_name}],
            "text": item.drug_name,
        },
        "subject": {"reference": patient_ref},
        "requester": {"reference": practitioner_ref},
        "authoredOn": rx.prescribed_at.isoformat() if rx.prescribed_at else timezone.now().isoformat(),
        "dosageInstruction": [{
            "text": item.sig,
            "route": {"text": item.route},
            "timing": {"code": {"text": item.frequency}},
            "doseAndRate": [{"doseQuantity": {"value": _num(item.dose), "unit": item.dose_unit}}],
        }],
        "dispenseRequest": {
            "numberOfRepeatsAllowed": rx.refills_authorized,
            "quantity": {"value": float(item.quantity), "unit": item.quantity_unit},
            **({"expectedSupplyDuration": {"value": item.days_supply, "unit": "days"}}
               if item.days_supply else {}),
        },
        "substitution": {"allowedBoolean": bool(item.substitution_allowed and not item.dispense_as_written)},
    }
    if rx.diagnosis_codes:
        req["reasonCode"] = [{"coding": [{"system": "http://id.who.int/icd/release/11/mms", "code": str(c)}]}
                             for c in rx.diagnosis_codes]
    if rx.is_controlled:
        req["category"] = [{"text": f"controlled-schedule-{rx.dea_schedule}"}]
    return req


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def build_bundle(rx, *, network: str) -> dict:
    patient_ref = f"Patient/{rx.patient_id}"
    practitioner_ref = f"Practitioner/{rx.prescriber_id}"
    practitioner = {"resourceType": "Practitioner", "id": str(rx.prescriber_id), "identifier": []}
    if rx.prescriber_npi:
        practitioner["identifier"].append({"system": "urn:cymed:prescriber-license", "value": rx.prescriber_npi})
    if rx.prescriber_dea:
        practitioner["identifier"].append({"system": "urn:cymed:controlled-registration",
                                           "value": rx.prescriber_dea})
    entries = [{"fullUrl": f"urn:uuid:{item.id}",
                "resource": _medication_request(rx, item, patient_ref, practitioner_ref)}
               for item in rx.items.filter(is_active=True)]
    header = {
        "resourceType": "MessageHeader",
        "id": str(uuid.uuid4()),
        "eventCoding": {"system": "urn:cymed:erx-event", "code": "prescription-new"},
        "destination": [{"endpoint": f"urn:erx:{network}"}],
        "source": {"endpoint": f"urn:cymed:tenant:{rx.tenant_id}"},
        "focus": [{"reference": e["fullUrl"]} for e in entries],
    }
    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "message",
        "timestamp": timezone.now().isoformat(),
        "entry": [{"fullUrl": f"urn:uuid:{header['id']}", "resource": header},
                  {"fullUrl": f"urn:uuid:{rx.prescriber_id}", "resource": practitioner},
                  *entries],
    }
