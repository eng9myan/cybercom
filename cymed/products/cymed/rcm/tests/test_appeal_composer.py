"""Unit tests for AppealComposer.compose().

Renders the Django template with sample claim + denial codes + narrative and
asserts the resulting HTML contains the expected substitutions.
"""
from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID


def _make_claim(**overrides):
    defaults = dict(
        claim_number="CLM-APPEAL-001",
        patient_profile_id=UUID("11111111-1111-1111-1111-111111111111"),
        payer_code="TAWUNIYA",
        charge_total=Decimal("1234.56"),
        created_at=_dt.datetime(2026, 3, 15, 10, 30, 0),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ── django settings bootstrap ───────────────────────────────────────────────
def _ensure_django_configured():
    """The template engine needs a configured Django before Template()."""
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            DEBUG=False,
            TEMPLATES=[{
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "OPTIONS": {},
            }],
            USE_TZ=True,
        )
        django.setup()


# ── Rendering assertions ────────────────────────────────────────────────────
def test_compose_renders_claim_header_fields():
    _ensure_django_configured()
    from products.cymed.rcm.engines.appeals import AppealComposer

    claim = _make_claim()
    html = AppealComposer().compose(
        claim=claim,
        denial_codes=[{"carc": "CO-16", "note": "Missing information"}],
        narrative="Clinical notes support medical necessity.",
    )

    assert "CLM-APPEAL-001" in html
    assert "11111111-1111-1111-1111-111111111111" in html
    assert "TAWUNIYA" in html
    assert "1234.56" in html
    assert "2026-03-15" in html


def test_compose_renders_all_denial_codes_in_list():
    _ensure_django_configured()
    from products.cymed.rcm.engines.appeals import AppealComposer

    denial_codes = [
        {"carc": "CO-16", "note": "Missing information"},
        {"carc": "CO-97", "note": "Bundled into paid procedure"},
        {"carc": "CO-45", "note": "Charge exceeds fee schedule"},
    ]

    html = AppealComposer().compose(
        claim=_make_claim(),
        denial_codes=denial_codes,
        narrative="See documentation attached.",
    )

    for d in denial_codes:
        assert d["carc"] in html
        assert d["note"] in html


def test_compose_renders_narrative_verbatim():
    _ensure_django_configured()
    from products.cymed.rcm.engines.appeals import AppealComposer

    narrative = (
        "Patient underwent an emergent cholecystectomy on 2026-03-15; "
        "the preauth was verbally approved by adjuster #4471."
    )

    html = AppealComposer().compose(
        claim=_make_claim(),
        denial_codes=[{"carc": "CO-197", "note": "Auth required"}],
        narrative=narrative,
    )

    assert narrative in html


def test_compose_lists_supporting_docs_when_provided():
    _ensure_django_configured()
    from products.cymed.rcm.engines.appeals import AppealComposer

    html = AppealComposer().compose(
        claim=_make_claim(),
        denial_codes=[{"carc": "CO-50", "note": "Not medically necessary"}],
        narrative="Clinical justification below.",
        supporting_docs=[
            {"name": "operative_report.pdf"},
            {"name": "labs_2026-03-14.pdf"},
        ],
    )

    assert "operative_report.pdf" in html
    assert "labs_2026-03-14.pdf" in html


def test_compose_defaults_prepared_by_to_cymed_rcm():
    _ensure_django_configured()
    from products.cymed.rcm.engines.appeals import AppealComposer

    html = AppealComposer().compose(
        claim=_make_claim(),
        denial_codes=[{"carc": "CO-16", "note": "Missing info"}],
        narrative="Please reconsider.",
    )

    assert "CyMed RCM" in html


def test_compose_uses_custom_prepared_by_when_provided():
    _ensure_django_configured()
    from products.cymed.rcm.engines.appeals import AppealComposer

    html = AppealComposer().compose(
        claim=_make_claim(),
        denial_codes=[{"carc": "CO-16", "note": "Missing info"}],
        narrative="Please reconsider.",
        prepared_by="Dr. Aisha Al-Farsi, Appeals Coordinator",
    )

    assert "Dr. Aisha Al-Farsi, Appeals Coordinator" in html
    assert "CyMed RCM" not in html


def test_compose_includes_policy_clause_reference():
    """Every rendered appeal should cite the reconsideration policy clause."""
    _ensure_django_configured()
    from products.cymed.rcm.engines.appeals import AppealComposer

    html = AppealComposer().compose(
        claim=_make_claim(),
        denial_codes=[{"carc": "CO-16", "note": "Missing info"}],
        narrative="Reconsideration requested.",
    )

    assert "4.2" in html
    assert "Reconsideration" in html


def test_compose_handles_empty_denial_codes_and_docs():
    """Template must render cleanly with no denial rows or supporting docs."""
    _ensure_django_configured()
    from products.cymed.rcm.engines.appeals import AppealComposer

    html = AppealComposer().compose(
        claim=_make_claim(),
        denial_codes=[],
        narrative="Blanket reconsideration request.",
    )

    assert "Appeal" in html
    assert "Blanket reconsideration request." in html
    # No denial <li>s should render when list is empty
    assert "<li><strong>" not in html
