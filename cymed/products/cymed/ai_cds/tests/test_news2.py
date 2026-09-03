"""NEWS2 (Royal College of Physicians early warning score) scoring tests.

These tests exercise the pure scoring math inside ``NEWS2Engine.compute``.
The persistence side-effect (``_persist`` -> ``RiskScore.objects.create``) is
monkeypatched out so the tests are hermetic and independent of whether the
``cymed_ai_cds`` app has migrations in the test DB.
"""
from __future__ import annotations

import uuid

import pytest


def _install_fake_persist(monkeypatch, engine):
    """Replace ``engine._persist`` with an in-memory shim.

    The real implementation persists a ``RiskScore`` row before returning
    the result dict.  We only care about the scoring math here.
    """
    def fake_persist(*, patient_id, encounter_id, value, band, features, model_version="v1"):
        return {
            "id": "test-id",
            "score": float(value),
            "band": band,
            "type": engine.score_type,
            "features": features,
            "model_version": model_version,
        }
    monkeypatch.setattr(engine, "_persist", fake_persist)


def test_news2_normal_vitals_scores_zero(monkeypatch):
    """A fully-well patient must yield NEWS2 = 0 in the ``low`` band."""
    from products.cymed.ai_cds.engines.risk_scores import NEWS2Engine, Vitals

    engine = NEWS2Engine()
    _install_fake_persist(monkeypatch, engine)

    vitals = Vitals(
        hr=70, sbp=120, rr=16, temp_c=37.0, spo2=98,
        o2_supplement=False, consciousness="A",
    )
    result = engine.compute(
        patient_id=uuid.uuid4(), encounter_id=uuid.uuid4(), v=vitals,
    )

    assert result["type"] == "news2"
    assert result["score"] == 0
    assert result["band"] == "low"


def test_news2_septic_vitals_scores_high(monkeypatch):
    """Textbook deteriorating patient (RR 30, SpO2 90, temp 39, BP 90/50).

    Per RCP scoring: RR>=25 -> 3, SpO2<=91 -> 3, temp in [38.1,39.0] -> 1,
    SBP<=90 -> 3.  Total = 10 which is comfortably in the ``high`` band
    (>6) and would trigger an urgent clinical response.
    """
    from products.cymed.ai_cds.engines.risk_scores import NEWS2Engine, Vitals

    engine = NEWS2Engine()
    _install_fake_persist(monkeypatch, engine)

    vitals = Vitals(
        hr=88, sbp=90, rr=30, temp_c=39.0, spo2=90,
        o2_supplement=False, consciousness="A",
    )
    result = engine.compute(
        patient_id=uuid.uuid4(), encounter_id=uuid.uuid4(), v=vitals,
    )

    # 3 (RR) + 3 (SpO2) + 1 (temp) + 3 (SBP) = 10
    assert result["score"] == 10
    assert result["band"] == "high"


@pytest.mark.parametrize(
    ("vitals_kwargs", "expected_band"),
    [
        # Low band: NEWS2 <= 4
        (dict(hr=70, sbp=120, rr=16, temp_c=37.0, spo2=98), "low"),
        # Medium band: 5 <= NEWS2 <= 6
        # rr=22 (+2), spo2=94 (+1), sbp=100 (+2) => 5
        (dict(hr=70, sbp=100, rr=22, temp_c=37.0, spo2=94), "medium"),
        # High band: NEWS2 >= 7
        (dict(hr=140, sbp=85, rr=30, temp_c=35.0, spo2=90), "high"),
    ],
)
def test_news2_band_boundaries(monkeypatch, vitals_kwargs, expected_band):
    from products.cymed.ai_cds.engines.risk_scores import NEWS2Engine, Vitals

    engine = NEWS2Engine()
    _install_fake_persist(monkeypatch, engine)

    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        v=Vitals(**vitals_kwargs),
    )
    assert result["band"] == expected_band


def test_news2_altered_consciousness_adds_three_points(monkeypatch):
    """A non-"A" consciousness value must contribute exactly 3 points."""
    from products.cymed.ai_cds.engines.risk_scores import NEWS2Engine, Vitals

    engine = NEWS2Engine()
    _install_fake_persist(monkeypatch, engine)

    baseline = engine.compute(
        patient_id=uuid.uuid4(), encounter_id=uuid.uuid4(),
        v=Vitals(hr=70, sbp=120, rr=16, temp_c=37.0, spo2=98,
                 consciousness="A"),
    )
    altered = engine.compute(
        patient_id=uuid.uuid4(), encounter_id=uuid.uuid4(),
        v=Vitals(hr=70, sbp=120, rr=16, temp_c=37.0, spo2=98,
                 consciousness="V"),
    )
    assert altered["score"] - baseline["score"] == 3


def test_news2_supplemental_oxygen_adds_two_points(monkeypatch):
    from products.cymed.ai_cds.engines.risk_scores import NEWS2Engine, Vitals

    engine = NEWS2Engine()
    _install_fake_persist(monkeypatch, engine)

    room_air = engine.compute(
        patient_id=uuid.uuid4(), encounter_id=uuid.uuid4(),
        v=Vitals(hr=70, sbp=120, rr=16, temp_c=37.0, spo2=98,
                 o2_supplement=False),
    )
    on_o2 = engine.compute(
        patient_id=uuid.uuid4(), encounter_id=uuid.uuid4(),
        v=Vitals(hr=70, sbp=120, rr=16, temp_c=37.0, spo2=98,
                 o2_supplement=True),
    )
    assert on_o2["score"] - room_air["score"] == 2
