"""Unit tests for DenialPredictor.

Focuses on the deterministic scoring rules and the risk→recommendation
mapping (submit / review_then_submit / route_to_coder / hold_and_fix).
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace


def _make_claim(**overrides):
    defaults = dict(
        payer_code="OTHER",
        procedure_codes=[{"cpt": "99213", "modifier": "25", "qty": 1}],
        charge_total=Decimal("100.00"),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── Recommendation mapping ─────────────────────────────────────────────────
def test_recommend_submit_when_risk_below_15pct():
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    assert DenialPredictor()._recommend(0.0) == "submit"
    assert DenialPredictor()._recommend(0.10) == "submit"
    assert DenialPredictor()._recommend(0.149) == "submit"


def test_recommend_review_then_submit_between_15_and_35pct():
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    assert DenialPredictor()._recommend(0.15) == "review_then_submit"
    assert DenialPredictor()._recommend(0.30) == "review_then_submit"
    assert DenialPredictor()._recommend(0.349) == "review_then_submit"


def test_recommend_route_to_coder_between_35_and_60pct():
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    assert DenialPredictor()._recommend(0.35) == "route_to_coder"
    assert DenialPredictor()._recommend(0.50) == "route_to_coder"
    assert DenialPredictor()._recommend(0.599) == "route_to_coder"


def test_recommend_hold_and_fix_at_60pct_and_above():
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    assert DenialPredictor()._recommend(0.60) == "hold_and_fix"
    assert DenialPredictor()._recommend(0.85) == "hold_and_fix"
    assert DenialPredictor()._recommend(0.99) == "hold_and_fix"


# ── Score → prediction integration ─────────────────────────────────────────
def test_predict_clean_claim_yields_submit_recommendation():
    """Baseline + small payer prior stays under 15% → recommend submit."""
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    claim = _make_claim()  # OTHER payer prior = 0.03; modifier present
    result = DenialPredictor().predict(claim, scrub_errors=[])

    assert result["recommended_action"] == "submit"
    assert result["risk"] < 0.15
    assert result["model_version"].startswith("cymed-rcm-denial-baseline")


def test_predict_error_severity_scrub_bumps_risk_and_lists_driver():
    """A single 'error' scrub adds 0.25 → 0.05 + 0.25 + 0.03 (prior) = 0.33."""
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    claim = _make_claim()
    scrub_errors = [{"code": "MISSING_DX", "severity": "error"}]

    result = DenialPredictor().predict(claim, scrub_errors=scrub_errors)

    driver_factors = [d["factor"] for d in result["drivers"]]
    assert "MISSING_DX" in driver_factors
    assert result["risk"] >= 0.25
    assert result["recommended_action"] in ("review_then_submit", "route_to_coder")


def test_predict_warning_severity_scrub_adds_small_delta():
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    claim = _make_claim()
    scrub_errors = [{"code": "NO_PRIMARY_DX", "severity": "warning"}]

    result = DenialPredictor().predict(claim, scrub_errors=scrub_errors)

    warning_driver = next(d for d in result["drivers"] if d["factor"] == "NO_PRIMARY_DX")
    assert warning_driver["delta"] == 0.05


def test_predict_missing_modifier_produces_driver_per_procedure():
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    claim = _make_claim(procedure_codes=[
        {"cpt": "99213", "modifier": "", "qty": 1},
        {"cpt": "99214", "modifier": "", "qty": 1},
    ])
    result = DenialPredictor().predict(claim, scrub_errors=[])

    modifier_drivers = [d for d in result["drivers"] if d["factor"] == "MODIFIER_MISSING"]
    assert len(modifier_drivers) == 2
    assert {d["code"] for d in modifier_drivers} == {"99213", "99214"}


def test_predict_high_charge_adds_high_charge_driver():
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    claim = _make_claim(charge_total=Decimal("25000.00"))
    result = DenialPredictor().predict(claim, scrub_errors=[])

    factors = [d["factor"] for d in result["drivers"]]
    assert "HIGH_CHARGE" in factors


def test_predict_payer_prior_applies_higher_weight_for_known_payer():
    """MEDGULF prior (0.05) > OTHER prior (0.03), so risk should be higher."""
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    other = DenialPredictor().predict(_make_claim(payer_code="OTHER"), scrub_errors=[])
    medgulf = DenialPredictor().predict(_make_claim(payer_code="MEDGULF"), scrub_errors=[])

    assert medgulf["risk"] > other["risk"]
    factors = [d["factor"] for d in medgulf["drivers"]]
    assert "PAYER_PRIOR_MEDGULF" in factors


def test_predict_stacked_drivers_route_to_hold_and_fix():
    """Multiple errors + high charge + missing modifier → very high risk."""
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    claim = _make_claim(
        charge_total=Decimal("50000.00"),
        procedure_codes=[{"cpt": "99215", "modifier": "", "qty": 1}],
        payer_code="WALAA",
    )
    scrub_errors = [
        {"code": "MISSING_DX", "severity": "error"},
        {"code": "MISSING_PROC", "severity": "error"},
        {"code": "ZERO_CHARGE", "severity": "error"},
    ]

    result = DenialPredictor().predict(claim, scrub_errors=scrub_errors)

    assert result["recommended_action"] == "hold_and_fix"
    assert result["risk"] >= 0.60


def test_predict_risk_capped_at_99pct():
    """No matter how many drivers stack, risk must not exceed 0.99."""
    from products.cymed.rcm.engines.denial_predictor import DenialPredictor

    claim = _make_claim(
        charge_total=Decimal("100000.00"),
        procedure_codes=[{"cpt": f"{i}", "modifier": ""} for i in range(50)],
    )
    scrub_errors = [{"code": f"ERR{i}", "severity": "error"} for i in range(20)]

    result = DenialPredictor().predict(claim, scrub_errors=scrub_errors)

    assert result["risk"] <= 0.99
