"""Unit tests for ClaimScrubber rules.

Each test constructs a lightweight in-memory claim stand-in (SimpleNamespace)
so we can exercise every rule without paying the migration cost. The rules that
walk related models (DUPLICATE_CLAIM, POLICY_EXPIRED) are patched via
monkeypatch to isolate the scrubber logic under test.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest


# ── Helpers ─────────────────────────────────────────────────────────────────
def _make_claim(**overrides):
    """Return a minimal claim-like object accepted by ClaimScrubber.scrub().

    ClaimScrubber only touches attributes on the claim; using SimpleNamespace
    keeps the test hermetic from Django DB setup.
    """
    defaults = dict(
        id=uuid4(),
        encounter_id=uuid4(),
        patient_profile_id=uuid4(),
        claim_number="CLM-TEST-0001",
        payer_code="TAWUNIYA",
        payer_country="SA",
        diagnosis_codes=[{"icd11": "1A00", "primary": True}],
        procedure_codes=[{"cpt": "99213", "modifier": "", "qty": 1}],
        charge_total=Decimal("100.00"),
        status="draft",
    )
    defaults.update(overrides)
    # A fresh subclass per call: SimpleNamespace itself is immutable at the class
    # level, but a subclass is not — ClaimScrubber does `type(claim).objects`, and
    # tests attach a stub manager there. Fresh class per call keeps tests isolated.
    claim_cls = type("_ClaimStub", (SimpleNamespace,), {})
    return claim_cls(**defaults)


class _EmptyManager:
    """Stub Django manager that returns an empty queryset for every query."""

    def filter(self, *args, **kwargs):
        return self

    def exclude(self, *args, **kwargs):
        return self

    def exists(self):
        return False

    def first(self):
        return None


class _MatchingManager(_EmptyManager):
    """Manager stub that reports a prior submitted claim exists."""

    def exists(self):
        return True

    def first(self):
        return SimpleNamespace(claim_number="CLM-PRIOR-9999")


@pytest.fixture
def isolated_claim(monkeypatch):
    """Return a claim whose ORM manager and coverage lookup are stubbed off.

    Prevents accidental DB / apps.get_model calls during scrubber tests.
    """
    claim = _make_claim()

    # Bypass Coverage lookup entirely by making apps.get_model raise LookupError
    from products.cymed.rcm.engines import scrubber as scrubber_mod

    def _no_coverage(*args, **kwargs):
        raise LookupError("coverage disabled in test")

    monkeypatch.setattr(scrubber_mod.apps, "get_model", _no_coverage)

    # Attach an in-memory objects manager for the DUPLICATE_CLAIM check.
    # type(claim).objects is inspected inside the scrubber, so patch the class.
    claim_cls = type(claim)
    claim_cls.objects = _EmptyManager()
    return claim


# ── Rule tests ──────────────────────────────────────────────────────────────
def test_missing_dx_rule_flags_empty_diagnosis(isolated_claim):
    from products.cymed.rcm.engines.scrubber import ClaimScrubber

    isolated_claim.diagnosis_codes = []
    errors = ClaimScrubber().scrub(isolated_claim)

    codes = {e["code"] for e in errors}
    assert "MISSING_DX" in codes
    missing_dx = next(e for e in errors if e["code"] == "MISSING_DX")
    assert missing_dx["severity"] == "error"


def test_missing_proc_rule_flags_empty_procedures(isolated_claim):
    from products.cymed.rcm.engines.scrubber import ClaimScrubber

    isolated_claim.procedure_codes = []
    errors = ClaimScrubber().scrub(isolated_claim)

    codes = {e["code"] for e in errors}
    assert "MISSING_PROC" in codes
    proc = next(e for e in errors if e["code"] == "MISSING_PROC")
    assert proc["severity"] == "error"


def test_zero_charge_rule_flags_non_positive_total(isolated_claim):
    from products.cymed.rcm.engines.scrubber import ClaimScrubber

    isolated_claim.charge_total = Decimal("0.00")
    errors = ClaimScrubber().scrub(isolated_claim)

    codes = {e["code"] for e in errors}
    assert "ZERO_CHARGE" in codes


def test_missing_payer_rule_flags_blank_payer(isolated_claim):
    from products.cymed.rcm.engines.scrubber import ClaimScrubber

    isolated_claim.payer_code = ""
    errors = ClaimScrubber().scrub(isolated_claim)

    codes = {e["code"] for e in errors}
    assert "MISSING_PAYER" in codes


def test_no_primary_dx_rule_flags_when_no_primary_flag(isolated_claim):
    from products.cymed.rcm.engines.scrubber import ClaimScrubber

    isolated_claim.diagnosis_codes = [
        {"icd11": "1A00", "primary": False},
        {"icd11": "1B00", "primary": False},
    ]
    errors = ClaimScrubber().scrub(isolated_claim)

    codes = {e["code"] for e in errors}
    assert "NO_PRIMARY_DX" in codes
    warning = next(e for e in errors if e["code"] == "NO_PRIMARY_DX")
    assert warning["severity"] == "warning"


def test_duplicate_claim_rule_flags_when_prior_submitted_exists(monkeypatch):
    from products.cymed.rcm.engines import scrubber as scrubber_mod
    from products.cymed.rcm.engines.scrubber import ClaimScrubber

    monkeypatch.setattr(
        scrubber_mod.apps, "get_model",
        lambda *a, **k: (_ for _ in ()).throw(LookupError()),
    )

    claim = _make_claim()
    type(claim).objects = _MatchingManager()

    errors = ClaimScrubber().scrub(claim)

    codes = {e["code"] for e in errors}
    assert "DUPLICATE_CLAIM" in codes
    dup = next(e for e in errors if e["code"] == "DUPLICATE_CLAIM")
    assert "CLM-PRIOR-9999" in dup["message"]


def test_policy_expired_rule_flags_expired_coverage(monkeypatch):
    """Simulate an InsurancePolicy row whose valid_to is in the past."""
    from datetime import timedelta

    from django.utils import timezone

    from products.cymed.rcm.engines import scrubber as scrubber_mod
    from products.cymed.rcm.engines.scrubber import ClaimScrubber

    expired_policy = SimpleNamespace(
        valid_to=(timezone.now() - timedelta(days=1)).date(),
    )

    class _PolicyManager(_EmptyManager):
        def first(self):
            return expired_policy

    class _FakeCoverage:
        objects = _PolicyManager()

    monkeypatch.setattr(
        scrubber_mod.apps, "get_model",
        lambda app_label, model_name: _FakeCoverage,
    )

    claim = _make_claim()
    type(claim).objects = _EmptyManager()

    errors = ClaimScrubber().scrub(claim)

    codes = {e["code"] for e in errors}
    assert "POLICY_EXPIRED" in codes
    expired = next(e for e in errors if e["code"] == "POLICY_EXPIRED")
    assert expired["severity"] == "error"
    assert str(expired_policy.valid_to) in expired["message"]


def test_clean_claim_produces_no_errors(isolated_claim):
    """A well-formed claim with no coverage lookup should scrub clean."""
    from products.cymed.rcm.engines.scrubber import ClaimScrubber

    errors = ClaimScrubber().scrub(isolated_claim)

    codes = {e["code"] for e in errors}
    # None of the seven canonical rule codes should fire on a clean claim.
    problem_codes = {
        "MISSING_DX", "MISSING_PROC", "ZERO_CHARGE", "MISSING_PAYER",
        "NO_PRIMARY_DX", "DUPLICATE_CLAIM", "POLICY_EXPIRED",
    }
    assert not (codes & problem_codes), f"unexpected errors: {codes}"
