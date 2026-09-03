"""Morse Fall Scale banding tests (FallRiskEngine).

Reference bands used by the engine:
- score <  25 -> "low"
- 25 <= score < 45 -> "moderate"
- score >= 45 -> "high"
"""
from __future__ import annotations

import uuid

import pytest


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


@pytest.mark.parametrize(
    ("kwargs", "expected_score", "expected_band"),
    [
        # All benign -> 0 points -> low band
        (
            dict(
                history_of_fall=False,
                secondary_diagnosis=False,
                ambulatory_aid="none",
                iv_therapy=False,
                gait="normal",
                mental_status_impaired=False,
            ),
            0,
            "low",
        ),
        # Prior fall alone (25 pts) puts patient into moderate band boundary
        (
            dict(
                history_of_fall=True,
                secondary_diagnosis=False,
                ambulatory_aid="none",
                iv_therapy=False,
                gait="normal",
                mental_status_impaired=False,
            ),
            25,
            "moderate",
        ),
        # Prior fall (25) + secondary dx (15) + impaired gait (20) = 60 -> high
        (
            dict(
                history_of_fall=True,
                secondary_diagnosis=True,
                ambulatory_aid="none",
                iv_therapy=False,
                gait="impaired",
                mental_status_impaired=False,
            ),
            60,
            "high",
        ),
        # Furniture support alone = 30 pts -> moderate
        (
            dict(
                history_of_fall=False,
                secondary_diagnosis=False,
                ambulatory_aid="furniture",
                iv_therapy=False,
                gait="normal",
                mental_status_impaired=False,
            ),
            30,
            "moderate",
        ),
        # Weak gait (10) + IV (20) + secondary dx (15) = 45 -> high boundary
        (
            dict(
                history_of_fall=False,
                secondary_diagnosis=True,
                ambulatory_aid="none",
                iv_therapy=True,
                gait="weak",
                mental_status_impaired=False,
            ),
            45,
            "high",
        ),
    ],
)
def test_morse_scoring_and_bands(monkeypatch, kwargs, expected_score, expected_band):
    from products.cymed.ai_cds.engines.risk_scores import FallRiskEngine

    engine = FallRiskEngine()
    _install_fake_persist(monkeypatch, engine)

    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        **kwargs,
    )

    assert result["score"] == expected_score
    assert result["band"] == expected_band


def test_morse_unknown_ambulatory_aid_defaults_to_zero(monkeypatch):
    """Unrecognised ambulatory aid keys must not raise; they contribute 0."""
    from products.cymed.ai_cds.engines.risk_scores import FallRiskEngine

    engine = FallRiskEngine()
    _install_fake_persist(monkeypatch, engine)

    result = engine.compute(
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        history_of_fall=False,
        secondary_diagnosis=False,
        ambulatory_aid="wheelchair",  # not in the scoring dict
        iv_therapy=False,
        gait="normal",
        mental_status_impaired=False,
    )

    assert result["score"] == 0
    assert result["band"] == "low"
