"""Unit tests for the per-payer rule engines.

Covers TawuniyaRules, BupaRules, NSSFRules and the PayerRuleEngine dispatcher.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace


def _make_claim(**overrides):
    defaults = dict(
        payer_code="TAWUNIYA",
        payer_country="SA",
        fhir_payload={},
        charge_total=Decimal("100.00"),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── TawuniyaRules ───────────────────────────────────────────────────────────
def test_tawuniya_flags_missing_policy_expiry():
    from products.cymed.rcm.engines.payer_rules import TawuniyaRules

    claim = _make_claim(payer_code="TAWUNIYA", fhir_payload={})
    violations = TawuniyaRules().apply(claim)

    assert len(violations) == 1
    v = violations[0]
    assert v["code"] == "TAWUNIYA_MISSING_EXP"
    assert v["field"] == "fhir_payload.policy_expiry"


def test_tawuniya_passes_when_policy_expiry_present():
    from products.cymed.rcm.engines.payer_rules import TawuniyaRules

    claim = _make_claim(
        payer_code="TAWUNIYA",
        fhir_payload={"policy_expiry": "2026-12-31"},
    )
    violations = TawuniyaRules().apply(claim)

    assert violations == []


def test_tawuniya_handles_none_fhir_payload_gracefully():
    """`(claim.fhir_payload or {}).get(...)` should not crash on None."""
    from products.cymed.rcm.engines.payer_rules import TawuniyaRules

    claim = _make_claim(payer_code="TAWUNIYA", fhir_payload=None)
    violations = TawuniyaRules().apply(claim)

    assert len(violations) == 1
    assert violations[0]["code"] == "TAWUNIYA_MISSING_EXP"


# ── BupaRules ───────────────────────────────────────────────────────────────
def test_bupa_returns_no_violations_currently():
    """BupaRules is a placeholder — assert it explicitly returns []."""
    from products.cymed.rcm.engines.payer_rules import BupaRules

    claim = _make_claim(payer_code="BUPA")
    violations = BupaRules().apply(claim)

    assert violations == []
    assert BupaRules.payer_code == "BUPA"


# ── NSSFRules ───────────────────────────────────────────────────────────────
def test_nssf_flags_country_mismatch():
    from products.cymed.rcm.engines.payer_rules import NSSFRules

    claim = _make_claim(payer_code="NSSF", payer_country="SA")
    violations = NSSFRules().apply(claim)

    assert len(violations) == 1
    v = violations[0]
    assert v["code"] == "NSSF_COUNTRY_MISMATCH"
    assert v["field"] == "payer_country"


def test_nssf_passes_for_jordan():
    from products.cymed.rcm.engines.payer_rules import NSSFRules

    claim = _make_claim(payer_code="NSSF", payer_country="JO")
    violations = NSSFRules().apply(claim)

    assert violations == []


# ── PayerRuleEngine dispatcher ─────────────────────────────────────────────
def test_engine_dispatches_to_correct_rule_by_payer_code():
    from products.cymed.rcm.engines.payer_rules import PayerRuleEngine

    tawuniya_claim = _make_claim(payer_code="TAWUNIYA", fhir_payload={})
    nssf_claim = _make_claim(payer_code="NSSF", payer_country="SA")

    engine = PayerRuleEngine()

    tawuniya_violations = engine.check(tawuniya_claim)
    nssf_violations = engine.check(nssf_claim)

    assert any(v["code"] == "TAWUNIYA_MISSING_EXP" for v in tawuniya_violations)
    assert any(v["code"] == "NSSF_COUNTRY_MISMATCH" for v in nssf_violations)


def test_engine_returns_empty_for_unknown_payer():
    from products.cymed.rcm.engines.payer_rules import PayerRuleEngine

    claim = _make_claim(payer_code="UNKNOWN_PAYER_XYZ")
    violations = PayerRuleEngine().check(claim)

    assert violations == []


def test_engine_matches_payer_case_insensitively():
    """PayerRuleEngine.check() upper-cases the payer_code before lookup."""
    from products.cymed.rcm.engines.payer_rules import PayerRuleEngine

    claim = _make_claim(payer_code="tawuniya", fhir_payload={})
    violations = PayerRuleEngine().check(claim)

    assert any(v["code"] == "TAWUNIYA_MISSING_EXP" for v in violations)


def test_engine_registers_all_three_rule_sets():
    from products.cymed.rcm.engines.payer_rules import (
        BupaRules, NSSFRules, PayerRuleEngine, TawuniyaRules,
    )

    engine = PayerRuleEngine()

    assert isinstance(engine.rules["TAWUNIYA"], TawuniyaRules)
    assert isinstance(engine.rules["BUPA"], BupaRules)
    assert isinstance(engine.rules["NSSF"], NSSFRules)
