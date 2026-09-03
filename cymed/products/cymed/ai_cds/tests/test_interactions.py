"""Drug interaction / allergy / renal / pregnancy engine tests.

The engine persists ``CDSAlert`` rows via ``_alert``.  We monkeypatch that
sink so the tests do not depend on the ``cymed_ai_cds`` app schema being
migrated in the test DB.
"""
from __future__ import annotations

from decimal import Decimal


def _install_fake_alert_sink(monkeypatch, engine):
    """Replace ``_alert`` with an in-memory sink returning a plain dict."""
    def fake_alert(patient_id, kind, severity, title, detail, context):
        return {
            "id": "test-id",
            "patient_id": patient_id,
            "kind": kind,
            "severity": severity,
            "title": title,
            "detail": detail,
            "context": context,
        }
    monkeypatch.setattr(engine, "_alert", fake_alert)


def test_known_major_interaction_pair_detected(monkeypatch):
    """warfarin + aspirin is in KNOWN_MAJOR; must emit one high-severity
    drug_interaction alert when aspirin is newly ordered for a patient
    already on warfarin."""
    from products.cymed.ai_cds.engines.interactions import (
        DrugContext,
        InteractionEngine,
        PatientContext,
    )

    engine = InteractionEngine()
    _install_fake_alert_sink(monkeypatch, engine)

    patient = PatientContext(
        id="pt-1",
        active_meds=[DrugContext(rxnorm="rx-warfarin", name="warfarin")],
    )
    new_orders = [DrugContext(rxnorm="rx-aspirin", name="aspirin")]

    alerts = engine.check(patient, new_orders)

    interaction_alerts = [a for a in alerts if a["kind"] == "drug_interaction"]
    assert len(interaction_alerts) == 1, alerts
    alert = interaction_alerts[0]
    assert alert["severity"] == "high"
    assert alert["context"]["drug_a"].lower() == "aspirin"
    assert alert["context"]["drug_b"].lower() == "warfarin"


def test_known_major_interaction_case_insensitive(monkeypatch):
    """Order names differing only in case must still match KNOWN_MAJOR."""
    from products.cymed.ai_cds.engines.interactions import (
        DrugContext,
        InteractionEngine,
        PatientContext,
    )

    engine = InteractionEngine()
    _install_fake_alert_sink(monkeypatch, engine)

    patient = PatientContext(
        id="pt-2",
        active_meds=[DrugContext(rxnorm="rx-warfarin", name="Warfarin")],
    )
    alerts = engine.check(
        patient,
        [DrugContext(rxnorm="rx-clopidogrel", name="Clopidogrel")],
    )

    assert any(a["kind"] == "drug_interaction" for a in alerts)


def test_no_interaction_when_pair_unknown(monkeypatch):
    """A pair not in KNOWN_MAJOR must produce no drug_interaction alert."""
    from products.cymed.ai_cds.engines.interactions import (
        DrugContext,
        InteractionEngine,
        PatientContext,
    )

    engine = InteractionEngine()
    _install_fake_alert_sink(monkeypatch, engine)

    patient = PatientContext(
        id="pt-3",
        active_meds=[DrugContext(rxnorm="rx-paracetamol", name="paracetamol")],
    )
    alerts = engine.check(
        patient,
        [DrugContext(rxnorm="rx-loratadine", name="loratadine")],
    )
    assert [a for a in alerts if a["kind"] == "drug_interaction"] == []


def test_renal_adjust_emitted_for_low_egfr(monkeypatch):
    """metformin ordered for a patient with eGFR<30 must produce a
    renal_adjustment alert (RENAL_DOSE_ADJUST threshold for metformin
    is 30 ml/min)."""
    from products.cymed.ai_cds.engines.interactions import (
        DrugContext,
        InteractionEngine,
        PatientContext,
    )

    engine = InteractionEngine()
    _install_fake_alert_sink(monkeypatch, engine)

    patient = PatientContext(
        id="pt-ckd",
        egfr_ml_min=Decimal("20"),
    )
    alerts = engine.check(
        patient,
        [DrugContext(rxnorm="rx-metformin", name="metformin")],
    )

    renal = [a for a in alerts if a["kind"] == "renal_adjustment"]
    assert len(renal) == 1
    assert renal[0]["severity"] == "medium"
    assert renal[0]["context"]["drug"] == "metformin"
    assert renal[0]["context"]["egfr"] == "20"


def test_renal_adjust_suppressed_when_egfr_ok(monkeypatch):
    """metformin with eGFR at/above threshold must NOT alert."""
    from products.cymed.ai_cds.engines.interactions import (
        DrugContext,
        InteractionEngine,
        PatientContext,
    )

    engine = InteractionEngine()
    _install_fake_alert_sink(monkeypatch, engine)

    patient = PatientContext(id="pt-ok", egfr_ml_min=Decimal("60"))
    alerts = engine.check(
        patient,
        [DrugContext(rxnorm="rx-metformin", name="metformin")],
    )
    assert [a for a in alerts if a["kind"] == "renal_adjustment"] == []


def test_pregnancy_category_x_flagged(monkeypatch):
    """isotretinoin for a pregnant patient must emit a critical
    pregnancy_contraindication alert."""
    from products.cymed.ai_cds.engines.interactions import (
        DrugContext,
        InteractionEngine,
        PatientContext,
    )

    engine = InteractionEngine()
    _install_fake_alert_sink(monkeypatch, engine)

    patient = PatientContext(id="pt-preg", pregnancy_weeks=10)
    alerts = engine.check(
        patient,
        [DrugContext(rxnorm="rx-isotretinoin", name="isotretinoin")],
    )

    preg = [a for a in alerts if a["kind"] == "pregnancy_contraindication"]
    assert len(preg) == 1
    assert preg[0]["severity"] == "critical"
    assert preg[0]["context"]["pregnancy_weeks"] == 10


def test_allergy_produces_critical_alert(monkeypatch):
    """An order matching a documented allergy must produce a critical
    drug_allergy alert."""
    from products.cymed.ai_cds.engines.interactions import (
        DrugContext,
        InteractionEngine,
        PatientContext,
    )

    engine = InteractionEngine()
    _install_fake_alert_sink(monkeypatch, engine)

    patient = PatientContext(id="pt-al", allergies=["penicillin"])
    alerts = engine.check(
        patient,
        [DrugContext(rxnorm="rx-pen", name="Penicillin")],
    )

    allergy = [a for a in alerts if a["kind"] == "drug_allergy"]
    assert len(allergy) == 1
    assert allergy[0]["severity"] == "critical"
