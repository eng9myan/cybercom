"""qSOFA + SIRS sepsis screening tests (SepsisEngine).

The engine bundles both scores and bands them together.  We assert
known positive and negative cases for each half of the composite so a
regression in either sub-score is caught.
"""
from __future__ import annotations

import uuid


def _install_fake_persist(monkeypatch, engine):
    def fake_persist(*, patient_id, encounter_id, value, band, features, model_version="v1"):
        return {
            "id": "test-id",
            "score": float(value),
            "band": band,
            "type": engine.score_type,
            "features": features,
        }
    monkeypatch.setattr(engine, "_persist", fake_persist)


def test_qsofa_negative_low_band(monkeypatch):
    """Well patient: qSOFA=0, SIRS=0 -> low band."""
    from products.cymed.ai_cds.engines.risk_scores import SepsisEngine, Vitals

    engine = SepsisEngine()
    _install_fake_persist(monkeypatch, engine)

    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        v=Vitals(hr=70, sbp=120, rr=16, temp_c=37.0, wbc=8.0, consciousness="A"),
        suspected_infection=False,
    )

    assert result["features"]["qsofa"] == 0
    assert result["features"]["sirs"] == 0
    assert result["band"] == "low"
    assert result["score"] == 0


def test_qsofa_positive_high_band(monkeypatch):
    """qSOFA >= 2 -> high, regardless of suspected_infection."""
    from products.cymed.ai_cds.engines.risk_scores import SepsisEngine, Vitals

    engine = SepsisEngine()
    _install_fake_persist(monkeypatch, engine)

    # RR>=22 (+1), SBP<=100 (+1), altered consciousness (+1) => qSOFA = 3
    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        v=Vitals(hr=110, sbp=90, rr=24, temp_c=37.5, consciousness="V"),
        suspected_infection=False,
    )

    assert result["features"]["qsofa"] == 3
    assert result["band"] == "high"


def test_qsofa_single_point_moderate_band(monkeypatch):
    """qSOFA == 1 with no infection suspicion -> moderate band."""
    from products.cymed.ai_cds.engines.risk_scores import SepsisEngine, Vitals

    engine = SepsisEngine()
    _install_fake_persist(monkeypatch, engine)

    # Only RR>=22 counts -> qSOFA = 1
    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        v=Vitals(hr=88, sbp=130, rr=24, temp_c=37.0, consciousness="A"),
        suspected_infection=False,
    )

    assert result["features"]["qsofa"] == 1
    assert result["band"] == "moderate"


def test_sirs_negative_no_alert(monkeypatch):
    """Classic SIRS-negative: only 1 SIRS criterion, no infection."""
    from products.cymed.ai_cds.engines.risk_scores import SepsisEngine, Vitals

    engine = SepsisEngine()
    _install_fake_persist(monkeypatch, engine)

    # HR>90 alone => SIRS = 1
    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        v=Vitals(hr=95, sbp=130, rr=16, temp_c=37.0, wbc=8.0,
                 consciousness="A"),
        suspected_infection=True,
    )

    assert result["features"]["sirs"] == 1
    # SIRS < 2 and qSOFA == 0 -> low band
    assert result["band"] == "low"


def test_sirs_positive_with_infection_flags_high(monkeypatch):
    """>= 2 SIRS + suspected infection escalates to high band even when
    qSOFA is sub-threshold."""
    from products.cymed.ai_cds.engines.risk_scores import SepsisEngine, Vitals

    engine = SepsisEngine()
    _install_fake_persist(monkeypatch, engine)

    # temp>38 (+1), HR>90 (+1), RR>20 (+1), WBC>12 (+1) => SIRS = 4
    # qSOFA: RR>=22 (+1) only -> 1 (does NOT itself trigger high)
    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        v=Vitals(hr=105, sbp=125, rr=22, temp_c=38.5, wbc=14.0,
                 consciousness="A"),
        suspected_infection=True,
    )

    assert result["features"]["sirs"] == 4
    assert result["band"] == "high"


def test_sirs_positive_without_infection_does_not_escalate(monkeypatch):
    """SIRS >= 2 alone (no suspected infection) does not force high band."""
    from products.cymed.ai_cds.engines.risk_scores import SepsisEngine, Vitals

    engine = SepsisEngine()
    _install_fake_persist(monkeypatch, engine)

    # Same SIRS-positive vitals as above but infection flag off.
    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        v=Vitals(hr=105, sbp=125, rr=22, temp_c=38.5, wbc=14.0,
                 consciousness="A"),
        suspected_infection=False,
    )

    assert result["features"]["sirs"] >= 2
    # qSOFA is 1 -> moderate (not high) when infection is not suspected
    assert result["band"] == "moderate"
