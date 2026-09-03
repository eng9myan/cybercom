"""
Drug interaction + allergy + dose engine.

Rule-based baseline with hooks for external drug-knowledge databases
(First Databank, Lexicomp, DrugBank). Extend by plugging a `DrugKnowledgeBase`
implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from ..models import CDSAlert


@dataclass
class DrugContext:
    rxnorm: str
    name: str
    dose_mg: Decimal | None = None
    route: str = ""
    frequency: str = ""


@dataclass
class PatientContext:
    id: str
    weight_kg: Decimal | None = None
    age_years: Decimal | None = None
    pregnancy_weeks: int | None = None
    egfr_ml_min: Decimal | None = None                # renal function
    allergies: list[str] | None = None                # substances
    active_meds: list[DrugContext] | None = None


class InteractionEngine:
    """Baseline rules — replace / augment with commercial DB in production."""

    # Minimal starter interaction pairs (RxNorm code → set of codes).
    KNOWN_MAJOR = {
        ("warfarin", "aspirin"),
        ("warfarin", "clopidogrel"),
        ("warfarin", "amiodarone"),
        ("simvastatin", "clarithromycin"),
        ("sildenafil", "nitrates"),
        ("mao_inhibitor", "ssri"),
    }

    RENAL_DOSE_ADJUST = {
        # drug → (min_egfr, adjustment_note)
        "vancomycin": (Decimal("60"), "Adjust vancomycin dose in eGFR<60"),
        "gabapentin": (Decimal("60"), "Reduce gabapentin dose in CKD"),
        "metformin":  (Decimal("30"), "Stop metformin if eGFR<30"),
    }

    PREGNANCY_CATEGORY_X = {"isotretinoin", "warfarin", "misoprostol",
                             "methotrexate", "atorvastatin"}

    def check(self, patient: PatientContext, new_drugs: Iterable[DrugContext]) -> list[dict]:
        alerts = []

        active_names = {d.name.lower() for d in (patient.active_meds or [])}
        allergies = {a.lower() for a in (patient.allergies or [])}

        for d in new_drugs:
            dname = d.name.lower()

            # Allergy
            if dname in allergies:
                alerts.append(self._alert(
                    patient.id, "drug_allergy", "critical",
                    f"Patient allergic to {d.name}",
                    f"Ordered {d.name} — patient allergy on file.",
                    {"drug": d.name},
                ))

            # Interactions
            for other in active_names:
                if (dname, other) in self.KNOWN_MAJOR or (other, dname) in self.KNOWN_MAJOR:
                    alerts.append(self._alert(
                        patient.id, "drug_interaction", "high",
                        f"Major interaction: {d.name} + {other}",
                        f"{d.name} and {other} together carry major interaction risk.",
                        {"drug_a": d.name, "drug_b": other},
                    ))

            # Renal
            if patient.egfr_ml_min is not None:
                threshold_note = self.RENAL_DOSE_ADJUST.get(dname)
                if threshold_note and patient.egfr_ml_min < threshold_note[0]:
                    alerts.append(self._alert(
                        patient.id, "renal_adjustment", "medium",
                        f"Renal adjustment: {d.name}",
                        threshold_note[1] + f" (eGFR {patient.egfr_ml_min})",
                        {"drug": d.name, "egfr": str(patient.egfr_ml_min)},
                    ))

            # Pregnancy
            if patient.pregnancy_weeks and dname in self.PREGNANCY_CATEGORY_X:
                alerts.append(self._alert(
                    patient.id, "pregnancy_contraindication", "critical",
                    f"Category X in pregnancy: {d.name}",
                    f"{d.name} is contraindicated in pregnancy.",
                    {"drug": d.name, "pregnancy_weeks": patient.pregnancy_weeks},
                ))

            # Duplicate therapy
            if dname in active_names:
                alerts.append(self._alert(
                    patient.id, "duplicate_therapy", "medium",
                    f"Duplicate order: {d.name}",
                    f"{d.name} already on active med list.",
                    {"drug": d.name},
                ))

        return alerts

    def _alert(self, patient_id, kind, severity, title, detail, context):
        alert = CDSAlert.objects.create(
            patient_id=patient_id, kind=kind, severity=severity,
            title=title, detail=detail, context=context,
        )
        return {
            "id": str(alert.id),
            "kind": kind, "severity": severity,
            "title": title, "detail": detail, "context": context,
        }
