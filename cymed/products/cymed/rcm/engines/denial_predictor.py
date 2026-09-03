"""Denial risk predictor.

Baseline: logistic-style rule scoring on known denial drivers.
Later: replace `_score()` with trained gradient boosting model fed by
historical Claim837 + ClaimResponse rows.
"""
from __future__ import annotations

from decimal import Decimal


class DenialPredictor:
    model_version = "cymed-rcm-denial-baseline-v1"

    def predict(self, claim, scrub_errors: list[dict] | None = None) -> dict:
        risk, drivers = self._score(claim, scrub_errors or [])
        return {
            "risk": round(risk, 3),
            "drivers": drivers,
            "model_version": self.model_version,
            "recommended_action": self._recommend(risk),
        }

    def _score(self, claim, scrub_errors: list[dict]) -> tuple[float, list[dict]]:
        drivers = []
        risk = 0.05  # baseline

        # Scrub errors bump risk
        for e in scrub_errors:
            if e.get("severity") == "error":
                risk += 0.25
                drivers.append({"factor": e["code"], "delta": 0.25})
            elif e.get("severity") == "warning":
                risk += 0.05
                drivers.append({"factor": e["code"], "delta": 0.05})

        # Missing modifier on procedure codes
        for p in claim.procedure_codes:
            if not p.get("modifier"):
                risk += 0.03
                drivers.append({"factor": "MODIFIER_MISSING", "delta": 0.03,
                                "code": p.get("cpt")})

        # High charge amount = higher denial risk
        if claim.charge_total > Decimal("10000"):
            risk += 0.10
            drivers.append({"factor": "HIGH_CHARGE", "delta": 0.10})

        # Payer-specific historical patterns (placeholder)
        payer_priors = {"MEDGULF": 0.05, "WALAA": 0.08}
        prior = payer_priors.get(claim.payer_code.upper(), 0.03)
        risk += prior
        drivers.append({"factor": f"PAYER_PRIOR_{claim.payer_code}", "delta": prior})

        return min(risk, 0.99), drivers

    def _recommend(self, risk: float) -> str:
        if risk < 0.15: return "submit"
        if risk < 0.35: return "review_then_submit"
        if risk < 0.60: return "route_to_coder"
        return "hold_and_fix"
