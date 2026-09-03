"""Bedside risk scores — deterministic scoring today, ML-backed later.

Every engine returns a dict + persists a RiskScore row for trending.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..models import RiskScore


@dataclass
class Vitals:
    hr: int | None = None                   # bpm
    sbp: int | None = None                  # systolic BP
    rr: int | None = None                   # respirations
    temp_c: float | None = None
    spo2: int | None = None                 # %
    o2_supplement: bool = False
    consciousness: str = "A"                # A=alert, V=voice, P=pain, U=unresponsive
    gcs: int | None = None
    wbc: float | None = None
    lactate: float | None = None


class _BaseScoreEngine:
    score_type: str

    def _persist(self, *, patient_id, encounter_id, value, band,
                  features, model_version="v1") -> dict:
        s = RiskScore.objects.create(
            patient_id=patient_id, encounter_id=encounter_id,
            score_type=self.score_type, value=Decimal(str(value)),
            band=band, features=features, model_version=model_version,
        )
        return {"id": str(s.id), "score": float(value), "band": band,
                "type": self.score_type}


class NEWS2Engine(_BaseScoreEngine):
    """Royal College of Physicians NEWS2 — early warning score 0-20."""
    score_type = "news2"

    def compute(self, *, patient_id, encounter_id, v: Vitals) -> dict:
        pts = 0
        if v.rr is not None:
            pts += 3 if v.rr <= 8 or v.rr >= 25 else 2 if v.rr >= 21 else 1 if v.rr in (9, 10, 11) else 0
        if v.spo2 is not None:
            pts += 3 if v.spo2 <= 91 else 2 if v.spo2 <= 93 else 1 if v.spo2 <= 95 else 0
        if v.o2_supplement:
            pts += 2
        if v.temp_c is not None:
            pts += 3 if v.temp_c <= 35.0 else 2 if v.temp_c >= 39.1 else 1 if v.temp_c >= 38.1 or v.temp_c <= 36.0 else 0
        if v.sbp is not None:
            pts += 3 if v.sbp <= 90 or v.sbp >= 220 else 2 if v.sbp <= 100 else 1 if v.sbp <= 110 else 0
        if v.hr is not None:
            pts += 3 if v.hr <= 40 or v.hr >= 131 else 2 if v.hr >= 111 else 1 if v.hr >= 91 or v.hr <= 50 else 0
        if v.consciousness != "A":
            pts += 3

        band = "low" if pts <= 4 else "medium" if pts <= 6 else "high"
        return self._persist(patient_id=patient_id, encounter_id=encounter_id,
                              value=pts, band=band,
                              features={"vitals": v.__dict__})


class SepsisEngine(_BaseScoreEngine):
    """qSOFA + SIRS heuristic."""
    score_type = "sepsis"

    def compute(self, *, patient_id, encounter_id, v: Vitals,
                 suspected_infection: bool = False) -> dict:
        qsofa = 0
        if v.rr is not None and v.rr >= 22: qsofa += 1
        if v.sbp is not None and v.sbp <= 100: qsofa += 1
        if v.consciousness != "A" or (v.gcs is not None and v.gcs < 15): qsofa += 1

        sirs = 0
        if v.temp_c is not None and (v.temp_c > 38 or v.temp_c < 36): sirs += 1
        if v.hr is not None and v.hr > 90: sirs += 1
        if v.rr is not None and v.rr > 20: sirs += 1
        if v.wbc is not None and (v.wbc > 12 or v.wbc < 4): sirs += 1

        value = qsofa
        high_risk = qsofa >= 2 or (sirs >= 2 and suspected_infection)
        band = "high" if high_risk else "moderate" if qsofa == 1 else "low"
        return self._persist(patient_id=patient_id, encounter_id=encounter_id,
                              value=value, band=band,
                              features={"qsofa": qsofa, "sirs": sirs,
                                        "suspected_infection": suspected_infection})


class ReadmissionEngine(_BaseScoreEngine):
    """LACE score (Length of stay, Acuity, Comorbidity, ED visits) — 0-19."""
    score_type = "readmission_30d"

    def compute(self, *, patient_id, encounter_id, los_days: int,
                 emergency_admission: bool, charlson_index: int,
                 ed_visits_last_6mo: int) -> dict:
        L = 0 if los_days == 0 else 1 if los_days == 1 else 2 if los_days == 2 else 3 if los_days == 3 else 4 if los_days <= 6 else 5 if los_days <= 13 else 7
        A = 3 if emergency_admission else 0
        C = min(charlson_index, 5)
        E = min(ed_visits_last_6mo, 4)
        total = L + A + C + E
        band = "low" if total <= 4 else "moderate" if total <= 9 else "high"
        return self._persist(patient_id=patient_id, encounter_id=encounter_id,
                              value=total, band=band,
                              features={"L": L, "A": A, "C": C, "E": E})


class FallRiskEngine(_BaseScoreEngine):
    """Morse Fall Scale — 0-125."""
    score_type = "fall_morse"

    def compute(self, *, patient_id, encounter_id,
                 history_of_fall: bool, secondary_diagnosis: bool,
                 ambulatory_aid: str, iv_therapy: bool,
                 gait: str, mental_status_impaired: bool) -> dict:
        pts = 0
        pts += 25 if history_of_fall else 0
        pts += 15 if secondary_diagnosis else 0
        pts += {"none": 0, "crutches": 15, "cane": 15, "walker": 15, "furniture": 30}.get(ambulatory_aid, 0)
        pts += 20 if iv_therapy else 0
        pts += {"normal": 0, "weak": 10, "impaired": 20}.get(gait, 0)
        pts += 15 if mental_status_impaired else 0
        band = "low" if pts < 25 else "moderate" if pts < 45 else "high"
        return self._persist(patient_id=patient_id, encounter_id=encounter_id,
                              value=pts, band=band,
                              features={"history_of_fall": history_of_fall,
                                         "iv_therapy": iv_therapy,
                                         "gait": gait})
