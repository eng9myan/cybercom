"""LACE 30-day readmission score (ReadmissionEngine).

Reference banding used by the engine:
- L (Length of stay): 0d=0, 1d=1, 2d=2, 3d=3, 4-6d=4, 7-13d=5, 14+d=7
- A (Acuity/Emergency admission): +3 if True, else 0
- C (Charlson comorbidity index): capped at 5
- E (ED visits last 6 months): capped at 4
- Band: <=4 low, 5-9 moderate, >=10 high
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


def test_lace_short_stay_no_comorbidity_low_band(monkeypatch):
    """5-day elective admit, 0 Charlson, 0 ED visits, no acute.

    L = 4 (LOS in 4-6 bucket)
    A = 0 (not emergency)
    C = 0
    E = 0
    Total = 4 -> low band.
    """
    from products.cymed.ai_cds.engines.risk_scores import ReadmissionEngine

    engine = ReadmissionEngine()
    _install_fake_persist(monkeypatch, engine)

    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        los_days=5,
        emergency_admission=False,
        charlson_index=0,
        ed_visits_last_6mo=0,
    )

    assert result["features"]["L"] == 4
    assert result["features"]["A"] == 0
    assert result["features"]["C"] == 0
    assert result["features"]["E"] == 0
    assert result["score"] == 4
    assert result["band"] == "low"


def test_lace_long_stay_comorbid_er_frequent_flyer_high(monkeypatch):
    """7-day emergency admit, 3 Charlson, 4 ED visits.

    L = 5 (LOS in 7-13 bucket)
    A = 3 (emergency)
    C = 3
    E = 4
    Total = 15 -> high band (>=10).
    """
    from products.cymed.ai_cds.engines.risk_scores import ReadmissionEngine

    engine = ReadmissionEngine()
    _install_fake_persist(monkeypatch, engine)

    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        los_days=7,
        emergency_admission=True,
        charlson_index=3,
        ed_visits_last_6mo=4,
    )

    assert result["features"]["L"] == 5
    assert result["features"]["A"] == 3
    assert result["features"]["C"] == 3
    assert result["features"]["E"] == 4
    assert result["score"] == 15
    assert result["band"] == "high"


def test_lace_moderate_band_boundary(monkeypatch):
    """Score = 5 lands squarely in moderate band."""
    from products.cymed.ai_cds.engines.risk_scores import ReadmissionEngine

    engine = ReadmissionEngine()
    _install_fake_persist(monkeypatch, engine)

    # 2 (L=2 days) + 3 (emergency) + 0 + 0 = 5
    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        los_days=2,
        emergency_admission=True,
        charlson_index=0,
        ed_visits_last_6mo=0,
    )
    assert result["score"] == 5
    assert result["band"] == "moderate"


def test_lace_charlson_capped_at_five(monkeypatch):
    """Charlson index cannot contribute more than 5 to the total."""
    from products.cymed.ai_cds.engines.risk_scores import ReadmissionEngine

    engine = ReadmissionEngine()
    _install_fake_persist(monkeypatch, engine)

    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        los_days=0,
        emergency_admission=False,
        charlson_index=99,
        ed_visits_last_6mo=0,
    )
    assert result["features"]["C"] == 5


def test_lace_ed_visits_capped_at_four(monkeypatch):
    """ED visits cannot contribute more than 4 to the total."""
    from products.cymed.ai_cds.engines.risk_scores import ReadmissionEngine

    engine = ReadmissionEngine()
    _install_fake_persist(monkeypatch, engine)

    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        los_days=0,
        emergency_admission=False,
        charlson_index=0,
        ed_visits_last_6mo=42,
    )
    assert result["features"]["E"] == 4
