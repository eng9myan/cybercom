"""ICD-11 NLP suggestion engine tests.

The engine queries a ``terminology.Concept`` model that may or may not be
registered in the app registry (the platform.terminology app does not ship
one today; it is a future extension point).  We mock the ``_terminology``
hook to return a fake Concept manager so we can assert the search logic
in isolation.
"""
from __future__ import annotations


class _FakeQuerySet:
    """Slice-able, filter-able fake resembling a Django QuerySet."""

    def __init__(self, rows):
        self._rows = list(rows)

    def filter(self, **kwargs):
        rows = self._rows
        if "code_system__code" in kwargs:
            rows = [r for r in rows if r.code_system_code == kwargs["code_system__code"]]
        if "display__icontains" in kwargs:
            needle = kwargs["display__icontains"].lower()
            rows = [r for r in rows if needle in r.display.lower()]
        return _FakeQuerySet(rows)

    def __getitem__(self, item):
        return self._rows[item]

    def __iter__(self):
        return iter(self._rows)


class _FakeConceptRow:
    def __init__(self, code, display, code_system_code="icd11"):
        self.code = code
        self.display = display
        self.code_system_code = code_system_code


class _FakeConceptManager:
    def __init__(self, rows):
        self._rows = rows

    @property
    def objects(self):
        return _FakeQuerySet(self._rows)


def _make_fake_concept_model(rows):
    """Return an object that quacks like the ``terminology.Concept`` model."""
    class FakeConceptModel:
        objects = _FakeQuerySet(rows)
    return FakeConceptModel


def test_baseline_lookup_returns_matches_for_known_keyword(monkeypatch):
    """Feed a source_text containing a keyword present in a fake ICD-11
    concept and assert the suggestion is returned."""
    from products.cymed.ai_cds.engines.icd_nlp import ICDNLPEngine

    fake_rows = [
        _FakeConceptRow(code="CA22", display="Chronic obstructive pulmonary disease"),
        _FakeConceptRow(code="5A11", display="Type 2 diabetes mellitus"),
        _FakeConceptRow(code="BA00", display="Essential hypertension"),
    ]
    FakeConcept = _make_fake_concept_model(fake_rows)

    engine = ICDNLPEngine()
    monkeypatch.setattr(engine, "_terminology", lambda: FakeConcept)

    results = engine._baseline_lookup("patient has essential hypertension today", limit=5)

    assert len(results) >= 1
    codes = {r["icd11"] for r in results}
    assert "BA00" in codes
    match = next(r for r in results if r["icd11"] == "BA00")
    assert match["label"] == "Essential hypertension"
    assert match["matched_term"].lower() in match["label"].lower()
    assert 0.0 < match["confidence"] <= 1.0


def test_baseline_lookup_returns_empty_when_terminology_missing(monkeypatch):
    """When the terminology.Concept model is not registered, the engine
    must degrade gracefully to an empty result set."""
    from products.cymed.ai_cds.engines.icd_nlp import ICDNLPEngine

    engine = ICDNLPEngine()
    monkeypatch.setattr(engine, "_terminology", lambda: None)

    assert engine._baseline_lookup("severe pneumonia with sepsis") == []


def test_baseline_lookup_ignores_short_words(monkeypatch):
    """Words <= 4 chars are dropped as noise; a query composed only of
    short words must return no suggestions even if a concept would match."""
    from products.cymed.ai_cds.engines.icd_nlp import ICDNLPEngine

    fake_rows = [_FakeConceptRow(code="Z00", display="ill")]
    FakeConcept = _make_fake_concept_model(fake_rows)

    engine = ICDNLPEngine()
    monkeypatch.setattr(engine, "_terminology", lambda: FakeConcept)

    # All words <= 4 chars -> zero keywords extracted
    assert engine._baseline_lookup("he is ill now") == []


def test_baseline_lookup_deduplicates_by_icd11_code(monkeypatch):
    """A concept that would be hit by multiple keywords must appear once."""
    from products.cymed.ai_cds.engines.icd_nlp import ICDNLPEngine

    fake_rows = [
        _FakeConceptRow(code="CA40", display="pneumonia bacterial infection"),
    ]
    FakeConcept = _make_fake_concept_model(fake_rows)

    engine = ICDNLPEngine()
    monkeypatch.setattr(engine, "_terminology", lambda: FakeConcept)

    # Both 'pneumonia' and 'bacterial' and 'infection' are >4 chars and
    # all match the single row.
    results = engine._baseline_lookup("pneumonia bacterial infection suspected", limit=5)
    codes = [r["icd11"] for r in results]
    assert codes.count("CA40") == 1


def test_suggest_persists_and_returns_suggestions(monkeypatch):
    """``suggest`` composes the lookup and persistence hop; mock both and
    assert the wire-format dict is well-shaped."""
    from products.cymed.ai_cds.engines import icd_nlp as icd_nlp_module
    from products.cymed.ai_cds.engines.icd_nlp import ICDNLPEngine

    fake_rows = [_FakeConceptRow(code="BA00", display="Essential hypertension")]
    FakeConcept = _make_fake_concept_model(fake_rows)

    engine = ICDNLPEngine()
    monkeypatch.setattr(engine, "_terminology", lambda: FakeConcept)

    class _FakeRec:
        id = "rec-1"

    class _FakeManager:
        @staticmethod
        def create(**kwargs):
            _FakeManager.last_kwargs = kwargs
            return _FakeRec()

    monkeypatch.setattr(
        icd_nlp_module.ICDCodeSuggestion, "objects", _FakeManager,
    )

    out = engine.suggest(
        encounter_id="enc-1",
        source_text="patient has essential hypertension",
    )

    assert out["id"] == "rec-1"
    assert out["model_version"] == engine.model_version
    assert isinstance(out["suggestions"], list)
    assert any(s["icd11"] == "BA00" for s in out["suggestions"])
    # Persistence was invoked with the same suggestions payload
    assert _FakeManager.last_kwargs["suggestions"] == out["suggestions"]
    assert _FakeManager.last_kwargs["encounter_id"] == "enc-1"
