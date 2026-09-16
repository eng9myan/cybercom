"""
Regression tests for the MRAC parser against REAL ACARA v9 data.

Why this file exists: the original parser was built and tested against a
*synthetic* fixture. Its tests passed while the parser was, on real MRAC files,
(a) assigning year level 0 to every single outcome and (b) ingesting the
vocabulary root, strand headings and MRAC's own changelog entries as curriculum
outcomes. A synthetic fixture validates the spec, not reality — so these tests
run against verbatim nodes lifted from the published Mathematics and Numeracy
vocabularies.

Fixture provenance: nodes copied unmodified from
https://vocabulary.curriculum.edu.au/MRAC/2024/04/LA/MAT/export/.../MAT.jsonld
and .../GC/N/... (accessed 2026-08-09). Australian Curriculum content is
licensed CC BY 4.0; see mrac.ACARA_ATTRIBUTION.
"""

from pathlib import Path

import pytest

from products.cyed.curriculum import mrac

SAMPLES = Path(__file__).resolve().parent / "data" / "mrac_samples"
LA_SAMPLE = SAMPLES / "LA_MAT_sample.jsonld"
GC_SAMPLE = SAMPLES / "GC_N_sample.jsonld"


def _outcomes(path=LA_SAMPLE):
    return [r for r in mrac.parse_mrac(path) if r["kind"] == "outcome"]


def test_real_file_parses_at_all():
    """The published files are `[{"@graph": [...]}]` — an array-wrapped graph."""
    rows = list(mrac.parse_mrac(LA_SAMPLE))
    assert rows, "parser returned nothing for a real MRAC file"


def test_year_level_is_read_from_real_predicate():
    """
    Regression: every outcome came back as year 0 (Foundation) because the parser
    read asn:educationLevel, which does not appear in the published files. Year
    level is carried by dcterms:educationLevel / esa:nominalYearLevel.
    """
    outcomes = _outcomes()
    years = {o["year_level"] for o in outcomes}
    assert years != {0}, "all outcomes fell back to year 0 — year predicate not being read"
    # The sampled content description is a Year 10 measurement outcome.
    base = next(o for o in outcomes if o["code"] == "AC9M10M02")
    assert base["year_level"] == 10


def test_structural_nodes_are_not_ingested_as_outcomes():
    """
    Regression: the vocabulary root, strand/level/subject headings and changelog
    entries carry a statementNotation, so a `not code` guard does not exclude
    them. Only real curriculum statements may become outcomes.
    """
    outcomes = _outcomes()
    codes = [o["code"] for o in outcomes]
    assert "root" not in codes
    assert all(c.upper().startswith("AC9") for c in codes), \
        f"non-curriculum codes leaked in: {[c for c in codes if not c.upper().startswith('AC9')]}"
    # The changelog node's text must never appear as curriculum content.
    assert all("Corrected html tags" not in (o.get("content_description") or "") for o in outcomes)


def test_elaborations_link_to_their_parent():
    outcomes = _outcomes()
    elaborations = [o for o in outcomes if o.get("is_elaboration")]
    assert elaborations, "sample contains elaborations but none were flagged"
    for e in elaborations:
        assert e["code"].upper().startswith(e["parent_code"].upper())
        assert "_E" in e["code"].upper()


def test_general_capabilities_are_linked_from_skill_embodied():
    """asn:skillEmbodied points at /GC/<CODE>/<uuid> IRIs — this is the only
    way the capability many-to-many can be derived."""
    base = next(o for o in _outcomes() if o["code"] == "AC9M10M02")
    assert base["general_capability_codes"], "no general capabilities linked"
    assert "N" in base["general_capability_codes"] or "CCT" in base["general_capability_codes"]


def test_attribution_is_carried_on_every_row():
    """CC BY 4.0 requires attribution to travel with the data."""
    for row in mrac.parse_mrac(LA_SAMPLE):
        assert "ACARA" in row["attribution"]
        assert "CC BY 4.0" in row["attribution"]


def test_general_capability_vocabulary_parses():
    """GC files use their own notation (e.g. CCTANAC5) and carry no AC9 codes."""
    rows = list(mrac.parse_mrac(GC_SAMPLE))
    assert rows, "GC vocabulary produced no rows"


@pytest.mark.django_db
def test_loading_real_data_is_idempotent(tenant_id):
    """Re-running a load must update, never duplicate."""
    from products.cyed.curriculum.models import CurriculumOutcome

    mrac.load_mrac(tenant_id, LA_SAMPLE)
    first = CurriculumOutcome.objects.filter(tenant_id=tenant_id).count()
    assert first > 0

    mrac.load_mrac(tenant_id, LA_SAMPLE)
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == first


@pytest.mark.django_db
def test_loaded_rows_keep_their_year_level(tenant_id):
    """The year-level bug would have written every row as Foundation."""
    from products.cyed.curriculum.models import CurriculumOutcome

    mrac.load_mrac(tenant_id, LA_SAMPLE)
    outcome = CurriculumOutcome.objects.filter(tenant_id=tenant_id, code="AC9M10M02").first()
    assert outcome is not None
    assert outcome.year_level == 10
