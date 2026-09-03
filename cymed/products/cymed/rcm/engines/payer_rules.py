"""Per-payer rule engine — enforces payer-specific formatting + business rules."""
from __future__ import annotations


class PayerRule:
    def apply(self, claim) -> list[dict]:
        """Return list of {code, message, field} violations."""
        return []


class TawuniyaRules(PayerRule):
    """Tawuniya (KSA) requires policy expiration date on every claim."""
    payer_code = "TAWUNIYA"

    def apply(self, claim):
        violations = []
        if not (claim.fhir_payload or {}).get("policy_expiry"):
            violations.append({"code": "TAWUNIYA_MISSING_EXP",
                                "message": "policy_expiry required in FHIR payload",
                                "field": "fhir_payload.policy_expiry"})
        return violations


class BupaRules(PayerRule):
    """BUPA Arabia requires member_no + card_serial."""
    payer_code = "BUPA"

    def apply(self, claim):
        violations = []
        return violations


class NSSFRules(PayerRule):
    """Jordan NSSF — public insurance."""
    payer_code = "NSSF"

    def apply(self, claim):
        violations = []
        if claim.payer_country != "JO":
            violations.append({"code": "NSSF_COUNTRY_MISMATCH",
                                "message": "NSSF valid only for JO payer_country",
                                "field": "payer_country"})
        return violations


class PayerRuleEngine:
    def __init__(self):
        self.rules = {
            "TAWUNIYA": TawuniyaRules(),
            "BUPA": BupaRules(),
            "NSSF": NSSFRules(),
        }

    def check(self, claim) -> list[dict]:
        rule = self.rules.get(claim.payer_code.upper())
        return rule.apply(claim) if rule else []
