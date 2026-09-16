"""
Tests for the MRAC (Machine-Readable Australian Curriculum) ingester.

The fixtures below are hand-built in the SHAPE OF THE REAL ACARA EXPORTS:
array-wrapped ``@graph``, full-IRI predicate keys, list-valued objects with
``{"@value": ..., "@language": "en-au"}`` / ``{"@id": ...}``, ASN Statement
types, and an ``_E1`` elaboration of a base content description.

NOTHING here touches the network — the loader only ever reads local files or
already-parsed objects, and download_set() refuses to run without an explicit
allow_network=True.
"""

import copy
import json
import uuid

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from products.cyed.curriculum import mrac
from products.cyed.curriculum.models import (
    AchievementStandard,
    CrossCurriculumPriority,
    CurriculumOutcome,
    GeneralCapability,
    MracImportRun,
)

ASN = "http://purl.org/ASN/schema/core/"
DCT = "http://purl.org/dc/terms/"
SKOS = "http://www.w3.org/2004/02/skos/core#"

HOST = "https://vocabulary.curriculum.edu.au/MRAC/2024/04"
MAT = f"{HOST}/LA/MAT"
LEVEL = "http://purl.org/ASN/scheme/ASNEducationLevel"


def lit(value, lang="en-au"):
    return [{"@value": value, "@language": lang}]


def ref(iri):
    return [{"@id": iri}]


MAT_GRAPH = [
    {
        "@id": MAT,
        "@type": [SKOS + "ConceptScheme"],
        SKOS + "prefLabel": lit("Mathematics"),
        DCT + "title": lit("Mathematics"),
    },
    {
        "@id": f"{MAT}/Number",
        "@type": [SKOS + "Concept"],
        SKOS + "prefLabel": lit("Number"),
    },
    {
        "@id": f"{MAT}/Number/Year7",
        "@type": [SKOS + "Concept"],
        SKOS + "prefLabel": lit("Year 7 Number"),
        SKOS + "broader": ref(f"{MAT}/Number"),
    },
    {
        # Base content description.
        "@id": f"{MAT}/AC9M7N06",
        "@type": [ASN + "Statement", SKOS + "Concept"],
        ASN + "statementNotation": lit("AC9M7N06"),
        ASN + "statementLabel": lit("Content Description"),
        DCT + "description": lit(
            "Represent natural numbers as products of powers of prime numbers using exponent notation"
        ),
        ASN + "educationLevel": ref(f"{LEVEL}/7"),
        SKOS + "broader": ref(f"{MAT}/Number/Year7"),
        ASN + "skillEmbodied": [{"@id": f"{HOST}/GC/N/Element1"}, {"@id": f"{HOST}/GC/CCT"}],
        DCT + "subject": ref(f"{HOST}/CCP/S"),
    },
    {
        # Elaboration of the statement above (the _E<n> suffix is the link).
        "@id": f"{MAT}/AC9M7N06_E1",
        "@type": [ASN + "Statement"],
        ASN + "statementNotation": lit("AC9M7N06_E1"),
        ASN + "statementLabel": lit("Elaboration"),
        DCT + "description": lit("using exponent notation to represent 36 as 2 squared times 3 squared"),
        ASN + "educationLevel": ref(f"{LEVEL}/7"),
        SKOS + "broader": ref(f"{MAT}/AC9M7N06"),
    },
    {
        # Foundation statement — exercises the F -> year_level 0 mapping.
        "@id": f"{MAT}/AC9MFN01",
        "@type": [ASN + "Statement"],
        ASN + "statementNotation": lit("AC9MFN01"),
        DCT + "description": lit("Name, represent and order numbers to at least 20"),
        ASN + "educationLevel": ref(f"{LEVEL}/Foundation"),
        SKOS + "broader": ref(f"{MAT}/Number"),
    },
    {
        # The shared achievement standard for Mathematics Year 7.
        "@id": f"{MAT}/AchievementStandard/Year7",
        "@type": [ASN + "Statement"],
        ASN + "statementLabel": lit("Achievement Standard"),
        DCT + "description": lit("By the end of Year 7, students represent natural numbers as products."),
        ASN + "educationLevel": ref(f"{LEVEL}/7"),
    },
    {
        # An organiser with no notation — must be skipped, not imported.
        "@id": f"{MAT}/Number/Year7/Organiser",
        "@type": [SKOS + "Concept"],
        SKOS + "prefLabel": lit("Number organiser"),
    },
]

# Real shape: a LIST holding one object that carries @graph.
MAT_DOC = [{"@id": MAT, "@graph": MAT_GRAPH}]

GC_N_DOC = [
    {
        "@id": f"{HOST}/GC/N",
        "@graph": [
            {
                "@id": f"{HOST}/GC/N",
                "@type": [SKOS + "ConceptScheme"],
                SKOS + "prefLabel": lit("Numeracy"),
                DCT + "description": lit("Numeracy involves students recognising and understanding maths."),
            },
            {
                "@id": f"{HOST}/GC/N/Element1",
                "@type": [SKOS + "Concept"],
                SKOS + "prefLabel": lit("Number sense and algebra"),
            },
        ],
    }
]

CCP_S_DOC = [
    {
        "@id": f"{HOST}/CCP/S",
        "@graph": [
            {
                "@id": f"{HOST}/CCP/S",
                "@type": [SKOS + "ConceptScheme"],
                SKOS + "prefLabel": lit("Sustainability"),
                DCT + "description": lit("The Sustainability priority develops world views."),
            }
        ],
    }
]


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.fixture
def mrac_dir(tmp_path):
    """A directory of MRAC exports on disk, as an operator would have them."""
    (tmp_path / "LA_MAT.jsonld").write_text(json.dumps(MAT_DOC), encoding="utf-8")
    (tmp_path / "GC_N.jsonld").write_text(json.dumps(GC_N_DOC), encoding="utf-8")
    (tmp_path / "CCP_S.jsonld").write_text(json.dumps(CCP_S_DOC), encoding="utf-8")
    return tmp_path


def _by_kind(records, kind):
    return [r for r in records if r["kind"] == kind]


# ── extract_graph: the shape trap ────────────────────────────────────────────
def test_extract_graph_handles_the_real_array_wrapped_shape():
    nodes = mrac.extract_graph(MAT_DOC)
    assert len(nodes) == len(MAT_GRAPH)
    assert nodes[0]["@id"] == MAT


def test_extract_graph_handles_dict_and_bare_list_shapes():
    assert mrac.extract_graph({"@id": MAT, "@graph": MAT_GRAPH}) == MAT_GRAPH
    assert mrac.extract_graph(MAT_GRAPH) == MAT_GRAPH
    assert mrac.extract_graph([]) == []
    # A single bare node.
    assert mrac.extract_graph({"@id": MAT}) == [{"@id": MAT}]


def test_extract_graph_rejects_junk():
    with pytest.raises(mrac.MracParseError):
        mrac.extract_graph(None)
    with pytest.raises(mrac.MracParseError):
        mrac.extract_graph("not json-ld")
    with pytest.raises(mrac.MracParseError):
        mrac.extract_graph(42)


def test_parse_missing_file_raises():
    with pytest.raises(mrac.MracParseError):
        list(mrac.parse_mrac("D:/nope/does-not-exist.jsonld"))


# ── Parser ───────────────────────────────────────────────────────────────────
def test_parse_extracts_statements_with_full_iri_predicates():
    records = list(mrac.parse_mrac(MAT_DOC))
    outcomes = {r["code"]: r for r in _by_kind(records, "outcome")}

    # Only the three notated statements — the organiser and the concept
    # scheme are not outcomes.
    assert set(outcomes) == {"AC9M7N06", "AC9M7N06_E1", "AC9MFN01"}

    base = outcomes["AC9M7N06"]
    assert base["learning_area"] == "Mathematics"
    assert base["year_level"] == 7
    assert "exponent notation" in base["content_description"]
    assert base["is_elaboration"] is False
    assert base["parent_code"] is None
    # skos:broader chain -> strand is the outermost organiser.
    assert base["strand"] == "Number"
    assert base["sub_strand"] == "Year 7 Number"
    # Capability references are found across every object IRI, not one predicate.
    assert base["general_capability_codes"] == ["CCT", "N"]
    assert base["cross_curriculum_priority_codes"] == ["S"]
    assert base["source_uri"] == f"{MAT}/AC9M7N06"
    assert base["attribution"] == mrac.ACARA_ATTRIBUTION


def test_parse_detects_elaboration_and_its_parent():
    records = list(mrac.parse_mrac(MAT_DOC))
    elab = next(r for r in _by_kind(records, "outcome") if r["code"] == "AC9M7N06_E1")
    assert elab["is_elaboration"] is True
    assert elab["parent_code"] == "AC9M7N06"


def test_parse_maps_foundation_to_year_zero():
    records = list(mrac.parse_mrac(MAT_DOC))
    foundation = next(r for r in _by_kind(records, "outcome") if r["code"] == "AC9MFN01")
    assert foundation["year_level"] == 0


def test_parse_yields_achievement_standard():
    standards = _by_kind(list(mrac.parse_mrac(MAT_DOC)), "achievement_standard")
    assert len(standards) == 1
    assert standards[0]["learning_area"] == "Mathematics"
    assert standards[0]["year_level"] == 7
    assert standards[0]["standard_text"].startswith("By the end of Year 7")


def test_parse_is_identical_across_document_shapes():
    array_wrapped = list(mrac.parse_mrac(MAT_DOC))
    bare_object = list(mrac.parse_mrac({"@id": MAT, "@graph": MAT_GRAPH}))
    node_list = list(mrac.parse_mrac(MAT_GRAPH, set_code="LA/MAT"))
    assert array_wrapped == bare_object == node_list


def test_parse_reads_a_file_path_and_a_json_string(mrac_dir):
    from_path = list(mrac.parse_mrac(mrac_dir / "LA_MAT.jsonld"))
    from_string = list(mrac.parse_mrac(json.dumps(MAT_DOC), set_code="LA/MAT"))
    assert [r["kind"] for r in from_path] == [r["kind"] for r in from_string]
    assert len(_by_kind(from_path, "outcome")) == 3


def test_parse_gc_and_ccp_documents():
    gc = list(mrac.parse_mrac(GC_N_DOC))
    assert len(gc) == 1
    assert gc[0]["kind"] == "capability"
    assert gc[0]["code"] == "N"
    assert gc[0]["name"] == "Numeracy"
    assert "recognising" in gc[0]["description"]

    ccp = list(mrac.parse_mrac(CCP_S_DOC))
    assert ccp[0]["kind"] == "priority"
    assert ccp[0]["code"] == "S"
    assert ccp[0]["name"] == "Sustainability"


# ── Small pure helpers ───────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "raw,expected",
    [
        (f"{LEVEL}/7", 7),
        (f"{LEVEL}/Foundation", 0),
        ("F", 0),
        ("Year 10", 10),
        ("10", 10),
        ("", None),
        (None, None),
        ("tertiary", None),
        (f"{LEVEL}/99", None),
    ],
)
def test_normalise_year(raw, expected):
    assert mrac.normalise_year(raw) == expected


@pytest.mark.parametrize(
    "set_code,expected",
    [("LA/MAT", ("LA", "MAT")), ("MAT", ("LA", "MAT")), ("CCT", ("GC", "CCT")),
     ("CCP/S", ("CCP", "S")), ("GC_N", ("GC", "N")), ("", ("", ""))],
)
def test_split_set_code(set_code, expected):
    assert mrac.split_set_code(set_code) == expected


def test_area_from_code_disambiguates_hpe_from_hass():
    assert mrac.area_from_code("AC9HP4M01") == "Health and Physical Education"
    assert mrac.area_from_code("AC9HS7K01") == "Humanities and Social Sciences"
    assert mrac.area_from_code("AC9M7N06") == "Mathematics"
    assert mrac.area_from_code("XX1") == ""


def test_mrac_url_matches_the_published_pattern():
    assert mrac.mrac_url("LA/MAT") == (
        "https://vocabulary.curriculum.edu.au/MRAC/2024/04/LA/MAT/export/MRAC/2024/04/LA/MAT.jsonld"
    )
    assert mrac.mrac_url("GC/N", fmt="rdf").endswith("/GC/N.rdf")
    assert len(mrac.ALL_SETS) == 18


def test_download_refuses_without_explicit_network_opt_in(tmp_path):
    # If this ever hit the network the test suite would be non-hermetic.
    with pytest.raises(RuntimeError, match="allow_network"):
        mrac.download_set("LA/MAT", tmp_path)


# ── Loader ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_load_mrac_creates_outcomes_standards_and_links(tenant_id):
    result = mrac.load_mrac(tenant_id, MAT_DOC)

    assert result["outcomes_created"] == 3
    assert result["outcomes_updated"] == 0
    assert result["standards_upserted"] == 1
    assert result["elaborations_linked"] == 1
    assert result["set_code"] == "LA/MAT"
    assert result["attribution"] == mrac.ACARA_ATTRIBUTION

    base = CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06")
    assert base.learning_area == "Mathematics"
    assert base.year_level == 7
    assert base.strand == "Number"
    assert base.is_elaboration is False

    elab = CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06_E1")
    assert elab.is_elaboration is True
    assert str(elab.parent_outcome_id) == str(base.id)
    assert base.elaborations.count() == 1
    assert elab.elaboration == elab.content_description

    standard = AchievementStandard.objects.get(tenant_id=tenant_id, learning_area="Mathematics", year_level=7)
    base.refresh_from_db()
    assert str(base.achievement_standard_ref_id) == str(standard.id)
    # The Foundation outcome has no Year 7 standard, so it stays unlinked.
    assert CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9MFN01").achievement_standard_ref is None


@pytest.mark.django_db
def test_load_mrac_links_general_capabilities_and_priorities(tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC)
    base = CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06")

    assert sorted(base.general_capabilities.values_list("code", flat=True)) == ["CCT", "N"]
    assert list(base.cross_curriculum_priorities.values_list("code", flat=True)) == ["S"]
    # Stubs auto-created by the link get their canonical ACARA name.
    assert GeneralCapability.objects.get(tenant_id=tenant_id, code="CCT").name == "Critical and Creative Thinking"
    # The elaboration declares none, so it links to none.
    elab = CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06_E1")
    assert elab.general_capabilities.count() == 0


@pytest.mark.django_db
def test_gc_and_ccp_documents_enrich_capability_records(tenant_id):
    mrac.load_mrac(tenant_id, GC_N_DOC)
    mrac.load_mrac(tenant_id, CCP_S_DOC)
    mrac.load_mrac(tenant_id, MAT_DOC)

    numeracy = GeneralCapability.objects.get(tenant_id=tenant_id, code="N")
    assert numeracy.name == "Numeracy"
    assert "recognising" in numeracy.description
    assert numeracy.outcomes.filter(code="AC9M7N06").exists()

    sustainability = CrossCurriculumPriority.objects.get(tenant_id=tenant_id, code="S")
    assert sustainability.name == "Sustainability"
    assert sustainability.outcomes.count() == 1


@pytest.mark.django_db
def test_load_mrac_is_idempotent(tenant_id):
    first = mrac.load_mrac(tenant_id, MAT_DOC)
    second = mrac.load_mrac(tenant_id, MAT_DOC)
    third = mrac.load_mrac(tenant_id, MAT_DOC)

    assert first["outcomes_created"] == 3
    assert second["outcomes_created"] == 0
    assert second["outcomes_updated"] == 3
    assert third["outcomes_updated"] == 3

    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 3
    assert AchievementStandard.objects.filter(tenant_id=tenant_id).count() == 1
    assert GeneralCapability.objects.filter(tenant_id=tenant_id).count() == 2
    assert CrossCurriculumPriority.objects.filter(tenant_id=tenant_id).count() == 1

    base = CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06")
    # M2M links are set(), not add() — re-import must not accumulate duplicates.
    assert base.general_capabilities.count() == 2
    assert base.elaborations.count() == 1
    assert MracImportRun.objects.filter(tenant_id=tenant_id).count() == 3


@pytest.mark.django_db
def test_reimport_updates_changed_text(tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC)
    revised = copy.deepcopy(MAT_DOC)
    for node in revised[0]["@graph"]:
        if node.get(ASN + "statementNotation") == lit("AC9M7N06"):
            node[DCT + "description"] = lit("REVISED: represent natural numbers as products of primes")
    mrac.load_mrac(tenant_id, revised)

    base = CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06")
    assert base.content_description.startswith("REVISED:")
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 3


@pytest.mark.django_db
def test_load_mrac_records_attribution_on_the_import_run(tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC, set_code="LA/MAT")
    run = MracImportRun.objects.filter(tenant_id=tenant_id).first()
    assert run.attribution == mrac.ACARA_ATTRIBUTION
    assert "ACARA does not endorse" in run.attribution
    assert run.set_code == "LA/MAT"
    assert run.outcomes_created == 3


@pytest.mark.django_db
def test_load_mrac_tenant_isolation(tenant_id):
    other = uuid.uuid4()
    mrac.load_mrac(tenant_id, MAT_DOC)
    mrac.load_mrac(other, MAT_DOC)
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 3
    assert CurriculumOutcome.objects.filter(tenant_id=other).count() == 3
    mine = CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06")
    assert all(gc.tenant_id == tenant_id for gc in mine.general_capabilities.all())


@pytest.mark.django_db
def test_load_mrac_skips_statements_without_a_learning_area(tenant_id):
    # No set code anywhere and a code whose prefix is not an ACARA learning area.
    doc = [{"@graph": [{
        "@id": "urn:x/UNKNOWN1",
        "@type": [ASN + "Statement"],
        ASN + "statementNotation": lit("ZZ9X1"),
        DCT + "description": lit("Not an Australian Curriculum statement."),
    }]}]
    result = mrac.load_mrac(tenant_id, doc)
    assert result["statements_seen"] == 1
    assert result["skipped"] == 1
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 0


@pytest.mark.django_db
def test_load_directory_processes_capabilities_before_learning_areas(tenant_id, mrac_dir):
    bundle = mrac.load_mrac_directory(tenant_id, mrac_dir)

    assert len(bundle["files"]) == 3
    assert bundle["totals"]["outcomes_created"] == 3
    assert bundle["attribution"] == mrac.ACARA_ATTRIBUTION
    # GC/CCP first means the Numeracy name is already real when MAT links to it.
    assert GeneralCapability.objects.get(tenant_id=tenant_id, code="N").name == "Numeracy"

    again = mrac.load_mrac_directory(tenant_id, mrac_dir)
    assert again["totals"]["outcomes_created"] == 0
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 3


@pytest.mark.django_db
def test_load_directory_rejects_a_non_directory(tmp_path):
    with pytest.raises(mrac.MracParseError):
        mrac.load_mrac_directory(uuid.uuid4(), tmp_path / "nope")


# ── Management command ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_import_mrac_command_loads_a_directory(tenant_id, mrac_dir):
    call_command("import_mrac", tenant=str(tenant_id), dir=str(mrac_dir))
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 3
    assert GeneralCapability.objects.filter(tenant_id=tenant_id, code="N").exists()

    call_command("import_mrac", tenant=str(tenant_id), dir=str(mrac_dir))
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 3


@pytest.mark.django_db
def test_import_mrac_command_loads_a_single_file(tenant_id, mrac_dir):
    call_command("import_mrac", tenant=str(tenant_id), file=str(mrac_dir / "LA_MAT.jsonld"), set_code="LA/MAT")
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 3


@pytest.mark.django_db
def test_import_mrac_command_dry_run_writes_nothing(tenant_id, mrac_dir):
    call_command("import_mrac", tenant=str(tenant_id), dir=str(mrac_dir), dry_run=True)
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 0
    assert MracImportRun.objects.filter(tenant_id=tenant_id).count() == 0


@pytest.mark.django_db
def test_import_mrac_command_requires_a_source(tenant_id):
    from django.core.management.base import CommandError

    with pytest.raises(CommandError):
        call_command("import_mrac", tenant=str(tenant_id))
    with pytest.raises(CommandError):
        call_command("import_mrac", tenant=str(tenant_id), file="D:/nope/missing.jsonld")
    with pytest.raises(CommandError):
        # --download without a destination directory.
        call_command("import_mrac", tenant=str(tenant_id), download=True)


@pytest.mark.django_db
def test_existing_starter_import_still_works_alongside_mrac(tenant_id, mrac_dir):
    """Back-compat: the bundled 56-item starter set must keep loading."""
    call_command("import_curriculum", tenant=str(tenant_id))
    starter_count = CurriculumOutcome.objects.filter(tenant_id=tenant_id).count()
    assert starter_count >= 25
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id, is_elaboration=True).count() == 0

    # AC9MFN01 exists in BOTH the starter set and the MRAC fixture — it must be
    # updated in place, so only the two genuinely new codes are added.
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id, code="AC9MFN01").count() == 1
    call_command("import_mrac", tenant=str(tenant_id), dir=str(mrac_dir))

    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == starter_count + 2
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id, code="AC9MFN01").count() == 1
    # Nothing from the starter set was destroyed.
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id, code="AC9M7N01").exists()
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id, code="AC9E7LA01").exists()
    # ...and the MRAC-only structure landed on top of it.
    assert CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06_E1").parent_outcome is not None


# ── API ──────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_api_import_mrac_is_staff_only_and_idempotent(client_for, tenant_id):
    payload = {"document": MAT_DOC, "set_code": "LA/MAT"}

    parent = client_for(["parent"], email="p@home.com")
    assert parent.post("/api/v1/curriculum/outcomes/import-mrac/", payload, format="json").status_code == 403
    student = client_for(["student"], email="s@cyed.edu.au")
    assert student.post("/api/v1/curriculum/outcomes/import-mrac/", payload, format="json").status_code == 403

    admin = client_for(["tenant_admin"])
    first = admin.post("/api/v1/curriculum/outcomes/import-mrac/", payload, format="json")
    assert first.status_code == 200, first.data
    assert first.data["outcomes_created"] == 3
    assert first.data["attribution"] == mrac.ACARA_ATTRIBUTION

    second = admin.post("/api/v1/curriculum/outcomes/import-mrac/", payload, format="json")
    assert second.data["outcomes_created"] == 0
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id).count() == 3


@pytest.mark.django_db
def test_api_import_mrac_rejects_invalid_payloads(client_for):
    admin = client_for(["tenant_admin"])
    assert admin.post("/api/v1/curriculum/outcomes/import-mrac/", {}, format="json").status_code == 400
    bad = admin.post("/api/v1/curriculum/outcomes/import-mrac/", {"document": "junk"}, format="json")
    assert bad.status_code == 400


@pytest.mark.django_db
def test_coverage_endpoint_reports_acara_coverage(client_for, tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC)
    admin = client_for(["tenant_admin"])

    resp = admin.get("/api/v1/curriculum/outcomes/coverage/")
    assert resp.status_code == 200, resp.data
    data = resp.data
    assert data["total_outcomes"] == 3
    assert data["elaborations"] == 1
    assert data["content_descriptions"] == 2
    assert data["by_learning_area"] == [{"learning_area": "Mathematics", "count": 3}]
    assert {row["year_level"]: row["count"] for row in data["by_year_level"]} == {0: 1, 7: 2}
    assert {"learning_area": "Mathematics", "year_level": 7, "count": 2} in data["by_learning_area_and_year"]
    assert data["general_capabilities"] == 2
    assert data["cross_curriculum_priorities"] == 1
    assert data["achievement_standards"] == 1
    assert data["outcomes_linked_to_standard"] == 2
    assert data["import_runs"] == 1
    assert data["attribution"] == mrac.ACARA_ATTRIBUTION


@pytest.mark.django_db
def test_coverage_can_exclude_elaborations_and_filter_framework(client_for, tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC)
    admin = client_for(["tenant_admin"])

    excluded = admin.get("/api/v1/curriculum/outcomes/coverage/?include_elaborations=false")
    assert excluded.data["total_outcomes"] == 2
    assert excluded.data["elaborations"] == 0

    other = admin.get("/api/v1/curriculum/outcomes/coverage/?framework=NESA")
    assert other.data["total_outcomes"] == 0


@pytest.mark.django_db
def test_coverage_is_staff_only(client_for, tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC)
    assert client_for(["parent"], email="p@home.com").get(
        "/api/v1/curriculum/outcomes/coverage/").status_code == 403
    assert client_for(["teacher"]).get("/api/v1/curriculum/outcomes/coverage/").status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path", ["general-capabilities", "cross-curriculum-priorities", "achievement-standards", "mrac-runs"]
)
def test_reference_endpoints_are_staff_only_and_read_only(client_for, tenant_id, path):
    mrac.load_mrac(tenant_id, MAT_DOC)
    url = f"/api/v1/curriculum/{path}/"

    assert client_for(["parent"], email="p@home.com").get(url).status_code == 403
    assert client_for(["student"], email="s@cyed.edu.au").get(url).status_code == 403

    admin = client_for(["tenant_admin"])
    listed = admin.get(url)
    assert listed.status_code == 200
    rows = listed.data["results"] if isinstance(listed.data, dict) else listed.data
    assert len(rows) >= 1

    # Read-only router: writes are not routed at all.
    assert admin.post(url, {"code": "X", "name": "X"}, format="json").status_code == 405
    detail = f"{url}{rows[0]['id']}/"
    assert admin.get(detail).status_code == 200
    assert admin.delete(detail).status_code == 405


@pytest.mark.django_db
def test_reference_endpoints_are_tenant_isolated(client_for, tenant_id):
    mrac.load_mrac(uuid.uuid4(), MAT_DOC)  # another school's import
    admin = client_for(["tenant_admin"])
    resp = admin.get("/api/v1/curriculum/general-capabilities/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert rows == []


@pytest.mark.django_db
def test_outcome_filters_by_capability_priority_and_elaboration(client_for, tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC)
    admin = client_for(["tenant_admin"])

    def codes(query):
        resp = admin.get(f"/api/v1/curriculum/outcomes/{query}")
        assert resp.status_code == 200, resp.data
        rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
        return sorted(r["code"] for r in rows)

    assert codes("?general_capability=CCT") == ["AC9M7N06"]
    assert codes("?cross_curriculum_priority=S") == ["AC9M7N06"]
    assert codes("?elaborations=only") == ["AC9M7N06_E1"]
    assert codes("?elaborations=false") == ["AC9M7N06", "AC9MFN01"]
    assert codes("?parent_code=AC9M7N06") == ["AC9M7N06_E1"]
    assert codes("?general_capability=NOPE") == []


@pytest.mark.django_db
def test_outcome_serializer_exposes_capability_codes_and_elaboration_count(client_for, tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC)
    admin = client_for(["tenant_admin"])
    resp = admin.get("/api/v1/curriculum/outcomes/?code=AC9M7N06&elaborations=false")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    row = next(r for r in rows if r["code"] == "AC9M7N06")
    assert row["general_capability_codes"] == ["CCT", "N"]
    assert row["cross_curriculum_priority_codes"] == ["S"]
    assert row["elaboration_count"] == 1
    assert row["is_elaboration"] is False


@pytest.mark.django_db
def test_elaborations_detail_action(client_for, tenant_id):
    mrac.load_mrac(tenant_id, MAT_DOC)
    base = CurriculumOutcome.objects.get(tenant_id=tenant_id, code="AC9M7N06")
    admin = client_for(["tenant_admin"])
    resp = admin.get(f"/api/v1/curriculum/outcomes/{base.id}/elaborations/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["code"] == "AC9M7N06_E1"


@pytest.mark.django_db
def test_outcome_write_rejects_cross_tenant_relations(client_for, tenant_id):
    foreign = GeneralCapability.objects.create(tenant_id=uuid.uuid4(), code="N", name="Numeracy")
    admin = client_for(["tenant_admin"])
    resp = admin.post(
        "/api/v1/curriculum/outcomes/",
        {"code": "AC9M9N01", "learning_area": "Mathematics", "general_capabilities": [str(foreign.id)]},
        format="json",
    )
    assert resp.status_code == 400
    # The repo-wide exception handler flattens DRF field errors into `detail`.
    assert "general_capabilities" in str(resp.data)
    assert "different tenant" in str(resp.data)
    assert not CurriculumOutcome.objects.filter(tenant_id=tenant_id, code="AC9M9N01").exists()


@pytest.mark.django_db
def test_outcome_write_still_refuses_duplicate_codes(client_for, tenant_id):
    CurriculumOutcome.objects.create(tenant_id=tenant_id, code="AC9M8N01", learning_area="Mathematics")
    admin = client_for(["tenant_admin"])
    dup = admin.post(
        "/api/v1/curriculum/outcomes/",
        {"code": "AC9M8N01", "learning_area": "Mathematics"},
        format="json",
    )
    assert dup.status_code == 400
    assert "already exists" in str(dup.data)
    assert CurriculumOutcome.objects.filter(tenant_id=tenant_id, code="AC9M8N01").count() == 1
