"""
MRAC — Machine-Readable Australian Curriculum (ACARA v9) ingestion.

ACARA publishes the whole Australian Curriculum as SKOS/ASN vocabularies on a
PoolParty server at vocabulary.curriculum.edu.au. Each learning area, general
capability and cross-curriculum priority is one "vocabulary set". This module
parses those exports into normalised dicts and upserts them into the CyEd
curriculum registry.

Design notes that matter (learned the hard way from the real files):

  * The JSON-LD export parses to a **LIST containing one object** —
    ``[{"@graph": [...], "@id": "..."}]``. Code that does ``data.get("@graph")``
    raises AttributeError on a list. :func:`extract_graph` accepts every shape
    (array-wrapped, bare object, or a plain list of nodes).
  * Predicates are **full IRIs used as dict keys**, and every value is a
    **list** of ``{"@value": ..., "@language": "en-au"}`` or ``{"@id": ...}``.
    Never index a predicate directly.
  * Elaborations carry an ``_E<n>`` suffix on the statement notation:
    ``AC9M7N06_E1`` elaborates ``AC9M7N06``.
  * Mathematics alone is ~3.5 MB / 1949 graph nodes / 1289 AC9 statements, so
    the parser is a generator and the loader batches its lookups.

Network access is OPTIONAL and off by default: :func:`parse_mrac` and
:func:`load_mrac` only ever read a local path or an already-parsed object.
Downloading requires an explicit ``allow_network=True`` on :func:`download_set`.

LICENCE / ATTRIBUTION
    The Australian Curriculum is CC BY 4.0 (commercial use permitted) and the
    attribution notice below MUST accompany any use. It is stored on every
    :class:`~products.cyed.curriculum.models.MracImportRun` and emitted by the
    coverage API and the management command.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from django.db import transaction

from products.cyed.curriculum.models import (
    AchievementStandard,
    CrossCurriculumPriority,
    CurriculumOutcome,
    GeneralCapability,
    MracImportRun,
)

# ── Licence ──────────────────────────────────────────────────────────────────
ACARA_ATTRIBUTION = (
    "(c) Australian Curriculum, Assessment and Reporting Authority (ACARA) 2010 to "
    "present, unless otherwise indicated. This material was downloaded from the "
    "Australian Curriculum website (https://www.australiancurriculum.edu.au) and was "
    "modified. The material is licensed under CC BY 4.0 "
    "(https://creativecommons.org/licenses/by/4.0/). ACARA does not endorse any "
    "product that uses the Australian Curriculum."
)

# ── Where the files live ─────────────────────────────────────────────────────
MRAC_HOST = "https://vocabulary.curriculum.edu.au"
MRAC_VERSION = "MRAC/2024/04"

LEARNING_AREA_SETS = ["LA/ART", "LA/ENG", "LA/HPE", "LA/HASS", "LA/LAN", "LA/MAT", "LA/SCI", "LA/TEC"]
GENERAL_CAPABILITY_SETS = ["GC/CCT", "GC/DL", "GC/EU", "GC/IU", "GC/L", "GC/N", "GC/PSC"]
# CCP/S is verified. The other two priority set codes are best-effort — pass an
# explicit --set if a download 404s.
CROSS_CURRICULUM_PRIORITY_SETS = ["CCP/S", "CCP/ATSIHC", "CCP/AAEA"]
ALL_SETS = LEARNING_AREA_SETS + GENERAL_CAPABILITY_SETS + CROSS_CURRICULUM_PRIORITY_SETS

LEARNING_AREA_NAMES = {
    "ART": "The Arts",
    "ENG": "English",
    "HPE": "Health and Physical Education",
    "HASS": "Humanities and Social Sciences",
    "LAN": "Languages",
    "MAT": "Mathematics",
    "SCI": "Science",
    "TEC": "Technologies",
}
GENERAL_CAPABILITY_NAMES = {
    "CCT": "Critical and Creative Thinking",
    "DL": "Digital Literacy",
    "EU": "Ethical Understanding",
    "IU": "Intercultural Understanding",
    "L": "Literacy",
    "N": "Numeracy",
    "PSC": "Personal and Social Capability",
}
CROSS_CURRICULUM_PRIORITY_NAMES = {
    "S": "Sustainability",
    "ATSIHC": "Aboriginal and Torres Strait Islander Histories and Cultures",
    "AATSIHC": "Aboriginal and Torres Strait Islander Histories and Cultures",
    "AAEA": "Asia and Australia's Engagement with Asia",
    "AA": "Asia and Australia's Engagement with Asia",
}

# Learning area inferred from the AC9 code itself, longest prefix first, used
# when the vocabulary set cannot be determined from the file.
_CODE_AREA_PREFIXES = [
    ("AC9HP", "Health and Physical Education"),
    ("AC9H", "Humanities and Social Sciences"),
    ("AC9M", "Mathematics"),
    ("AC9E", "English"),
    ("AC9S", "Science"),
    ("AC9T", "Technologies"),
    ("AC9A", "The Arts"),
    ("AC9L", "Languages"),
]

# ── Vocabulary IRIs ──────────────────────────────────────────────────────────
ASN = "http://purl.org/ASN/schema/core/"
DCT = "http://purl.org/dc/terms/"
SKOS = "http://www.w3.org/2004/02/skos/core#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"

P_STATEMENT_NOTATION = ASN + "statementNotation"
P_STATEMENT_LABEL = ASN + "statementLabel"
P_EDUCATION_LEVEL = ASN + "educationLevel"
# Year level in the real MRAC files is carried by dcterms:educationLevel and by
# ESA's own predicate (a literal like "Year 7"), NOT by asn:educationLevel —
# which never appears. Reading only the ASN one yields year 0 for every row.
P_DCT_EDUCATION_LEVEL = DCT + "educationLevel"
P_NOMINAL_YEAR_LEVEL = "https://www.esa.edu.au/nominalYearLevel"
# Links a content description to the general capabilities / cross-curriculum
# priorities it embodies.
P_SKILL_EMBODIED = ASN + "skillEmbodied"
P_COMMENT = ASN + "comment"
P_DESCRIPTION = DCT + "description"
P_TITLE = DCT + "title"
P_SUBJECT = DCT + "subject"
P_PREF_LABEL = SKOS + "prefLabel"
P_ALT_LABEL = SKOS + "altLabel"
P_DEFINITION = SKOS + "definition"
P_BROADER = SKOS + "broader"
P_NOTATION = SKOS + "notation"
P_RDFS_LABEL = RDFS + "label"

T_STATEMENT = ASN + "Statement"
T_CONCEPT_SCHEME = SKOS + "ConceptScheme"

_LANG_PREFERENCE = ("en-au", "en-gb", "en", "")

_ELABORATION_RE = re.compile(r"^(?P<base>.+?)_E\d+$", re.IGNORECASE)
# asn:statementLabel values that mark an organiser/heading rather than a
# curriculum statement. Observed in the real MRAC v9 files alongside
# "Content Description", "Elaboration" and "Achievement Standard".
_ORGANISER_LABELS = {
    "strand", "sub-strand", "substrand", "level", "learning area", "subject",
    "root", "general capability", "element", "sub-element", "cross-curriculum priority",
    # Languages organises its content by pathway and year sequence; these are
    # headings ("F-10 Sequence", "First-Language Learner Pathway"), not outcomes.
    "sequence", "pathway",
}
# Note: filtering on an "AC9" code prefix would be WRONG — the Languages
# vocabulary legitimately issues non-AC9 codes (e.g. LANARA7-1) to real content
# descriptions and elaborations. statementLabel is the only safe discriminator.
# Notations used by structural nodes (vocabulary root, changelog entries).
_STRUCTURAL_CODES = {"root", "gc", "ccp", "la"}
_SET_IN_IRI_RE = re.compile(r"/(LA|GC|CCP)/([A-Za-z0-9_\-]{1,12})(?=[/#.]|$)", re.IGNORECASE)
_CAPABILITY_REF_RE = re.compile(r"/(GC|CCP)/([A-Za-z0-9_\-]{1,12})(?=[/#]|$)", re.IGNORECASE)
_YEAR_WORDS = {
    "f": 0, "fy": 0, "foundation": 0, "prep": 0, "k": 0, "kindergarten": 0,
    "reception": 0, "pre-primary": 0, "preprimary": 0, "transition": 0,
}

MAX_YEAR_LEVEL = 13


class MracParseError(ValueError):
    """The supplied document is not a usable MRAC export."""


# ── Low-level JSON-LD helpers ────────────────────────────────────────────────
def extract_graph(data) -> list:
    """
    Return the list of graph nodes from any shape the MRAC export shows up in.

    Real exports are ``[{"@graph": [...], "@id": ...}]`` (a LIST). Older/other
    tooling emits ``{"@graph": [...]}`` or a bare list of nodes. All are
    accepted; anything else raises :class:`MracParseError`.
    """
    if data is None:
        raise MracParseError("Empty MRAC document.")

    if isinstance(data, dict):
        graph = data.get("@graph")
        if isinstance(graph, list):
            return graph
        # A single bare node.
        return [data] if ("@id" in data or "@type" in data) else []

    if isinstance(data, list):
        if not data:
            return []
        wrappers = [d for d in data if isinstance(d, dict) and isinstance(d.get("@graph"), list)]
        if wrappers:
            nodes: list = []
            for wrapper in wrappers:
                nodes.extend(wrapper["@graph"])
            return nodes
        # A plain list of nodes.
        if all(isinstance(d, dict) for d in data):
            return list(data)

    raise MracParseError(f"Unrecognised MRAC JSON-LD shape: {type(data).__name__}")


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _literals(node: dict, *iris: str) -> list[str]:
    """All literal values for the first predicate present, language-ordered."""
    for iri in iris:
        values = _as_list(node.get(iri))
        if not values:
            continue
        ranked: list[tuple[int, str]] = []
        for value in values:
            if isinstance(value, dict):
                text = value.get("@value")
                if text is None:
                    continue
                lang = str(value.get("@language") or "").lower()
            elif isinstance(value, str):
                text, lang = value, ""
            else:
                continue
            try:
                rank = _LANG_PREFERENCE.index(lang)
            except ValueError:
                rank = len(_LANG_PREFERENCE)
            ranked.append((rank, str(text).strip()))
        if ranked:
            ranked.sort(key=lambda pair: pair[0])
            return [text for _, text in ranked if text]
    return []


def _literal(node: dict, *iris: str) -> str:
    values = _literals(node, *iris)
    return values[0] if values else ""


def _object_ids(node: dict, *iris: str) -> list[str]:
    out: list[str] = []
    for iri in iris:
        for value in _as_list(node.get(iri)):
            if isinstance(value, dict) and value.get("@id"):
                out.append(str(value["@id"]))
            elif isinstance(value, str) and "://" in value:
                out.append(value)
    return out


def _types(node: dict) -> list[str]:
    return [str(t) for t in _as_list(node.get("@type")) if isinstance(t, str)]


def is_statement(node: dict) -> bool:
    return T_STATEMENT in _types(node)


def normalise_year(raw) -> int | None:
    """
    ``".../ASNEducationLevel/7"`` → 7, ``".../Foundation"`` → 0, junk → None.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    segment = re.split(r"[/#]", text)[-1].strip().lower()
    if segment in _YEAR_WORDS:
        return 0
    match = re.search(r"(\d{1,2})", segment)
    if match:
        value = int(match.group(1))
        if 0 <= value <= MAX_YEAR_LEVEL:
            return value
    return None


_YEAR_PREDICATES = (P_EDUCATION_LEVEL, P_DCT_EDUCATION_LEVEL, P_NOMINAL_YEAR_LEVEL)


def _education_levels(node: dict) -> list[int]:
    raw = _object_ids(node, *_YEAR_PREDICATES) + _literals(node, *_YEAR_PREDICATES)
    years = {normalise_year(value) for value in raw}
    return sorted(y for y in years if y is not None)


def _referenced_capabilities(node: dict) -> tuple[list[str], list[str]]:
    """
    General-capability and cross-curriculum-priority codes referenced by this
    node, found by scanning *every* object IRI rather than relying on one
    predicate — MRAC links capabilities through several ASN/SKOS predicates and
    the set differs per learning area.
    """
    gcs: set[str] = set()
    ccps: set[str] = set()
    for key, value in node.items():
        if key in ("@id", "@type", "@context"):
            continue
        for item in _as_list(value):
            if isinstance(item, dict):
                iri = item.get("@id")
            elif isinstance(item, str):
                iri = item
            else:
                iri = None
            if not iri or "://" not in str(iri):
                continue
            for match in _CAPABILITY_REF_RE.finditer(str(iri)):
                group, code = match.group(1).upper(), match.group(2).upper()
                (gcs if group == "GC" else ccps).add(code)
    return sorted(gcs), sorted(ccps)


# ── Set / learning-area resolution ───────────────────────────────────────────
def split_set_code(set_code: str | None) -> tuple[str, str]:
    """``"LA/MAT"`` → ``("LA", "MAT")``; ``"CCT"`` → ``("GC", "CCT")``."""
    if not set_code:
        return "", ""
    parts = [p for p in re.split(r"[/\\_\-]", str(set_code).strip()) if p]
    if not parts:
        return "", ""
    if len(parts) >= 2 and parts[0].upper() in ("LA", "GC", "CCP"):
        return parts[0].upper(), parts[1].upper()
    code = parts[-1].upper()
    if code in LEARNING_AREA_NAMES:
        return "LA", code
    if code in GENERAL_CAPABILITY_NAMES:
        return "GC", code
    if code in CROSS_CURRICULUM_PRIORITY_NAMES:
        return "CCP", code
    return "", code


def infer_set_code(data, path: Path | None = None) -> str:
    """Best-effort ``"GROUP/CODE"`` from the document's @id, then the filename."""
    candidates: list[str] = []
    for wrapper in _as_list(data):
        if isinstance(wrapper, dict) and wrapper.get("@id"):
            candidates.append(str(wrapper["@id"]))
    if isinstance(data, dict) and data.get("@id"):
        candidates.append(str(data["@id"]))
    if path is not None:
        candidates.append(str(path).replace("\\", "/"))

    for candidate in candidates:
        match = _SET_IN_IRI_RE.search(candidate)
        if match:
            return f"{match.group(1).upper()}/{match.group(2).upper()}"

    if path is not None:
        group, code = split_set_code(path.stem)
        if group:
            return f"{group}/{code}"
    return ""


def area_from_code(code: str) -> str:
    upper = (code or "").upper()
    for prefix, area in _CODE_AREA_PREFIXES:
        if upper.startswith(prefix):
            return area
    return ""


# ── Parser ───────────────────────────────────────────────────────────────────
def _read_source(source):
    """Accept a path, a file-like object, a JSON string, or a parsed object."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if path.exists():
            with path.open("r", encoding="utf-8-sig") as handle:
                return json.load(handle), path
        if isinstance(source, str) and source.lstrip()[:1] in ("[", "{"):
            return json.loads(source), None
        raise MracParseError(f"MRAC file not found: {source}")
    if hasattr(source, "read"):
        return json.load(source), None
    return source, None


def _label_of(node: dict) -> str:
    return _literal(node, P_STATEMENT_LABEL, P_TITLE, P_PREF_LABEL, P_RDFS_LABEL)


def _looks_like_achievement_standard(node: dict) -> bool:
    if "achievement standard" in _label_of(node).lower():
        return True
    node_id = str(node.get("@id") or "").lower()
    return "/achievementstandard" in node_id or node_id.endswith("/as")


def _ancestor_labels(node: dict, index: dict, max_depth: int = 6) -> list[str]:
    """Labels of the SKOS broader chain, nearest ancestor first."""
    labels: list[str] = []
    seen: set[str] = set()
    current = node
    for _ in range(max_depth):
        parents = _object_ids(current, P_BROADER)
        if not parents:
            break
        parent_id = parents[0]
        if parent_id in seen:
            break
        seen.add(parent_id)
        parent = index.get(parent_id)
        if parent is None:
            break
        # Organisers only — a broader Statement with its own AC9 code is not a strand.
        if not _literal(parent, P_STATEMENT_NOTATION):
            label = _literal(parent, P_PREF_LABEL, P_TITLE, P_RDFS_LABEL, P_STATEMENT_LABEL)
            if label:
                labels.append(label)
        current = parent
    return labels


def parse_mrac(source, *, set_code: str | None = None, framework: str = "ACARA v9"):
    """
    Yield normalised records from one MRAC vocabulary export.

    ``source`` may be a file path, a file-like object, a JSON string, or an
    already-parsed object — **never a URL**; fetching is a separate, opt-in step
    (:func:`download_set`) so nothing in the normal path touches the network.

    Each record is a dict with a ``kind``:

    ``"outcome"``
        code, learning_area, subject, year_level, strand, sub_strand,
        content_description, is_elaboration, parent_code,
        general_capability_codes, cross_curriculum_priority_codes, source_uri
    ``"achievement_standard"``
        learning_area, subject, year_level, standard_text, source_uri
    ``"capability"`` / ``"priority"``
        code, name, description, source_uri
    """
    data, path = _read_source(source)
    graph = extract_graph(data)
    resolved_set = (set_code or infer_set_code(data, path) or "").strip()
    group, short_code = split_set_code(resolved_set)

    index = {str(node.get("@id")): node for node in graph if isinstance(node, dict) and node.get("@id")}

    default_area = LEARNING_AREA_NAMES.get(short_code, "") if group in ("", "LA") else ""

    # ── GC / CCP vocabularies describe one capability or priority ───────────
    if group in ("GC", "CCP") and short_code:
        scheme = next(
            (n for n in graph if isinstance(n, dict) and T_CONCEPT_SCHEME in _types(n)),
            None,
        )
        names = GENERAL_CAPABILITY_NAMES if group == "GC" else CROSS_CURRICULUM_PRIORITY_NAMES
        name = ""
        description = ""
        source_uri = ""
        if scheme is not None:
            name = _literal(scheme, P_PREF_LABEL, P_TITLE, P_RDFS_LABEL)
            description = _literal(scheme, P_DESCRIPTION, P_DEFINITION, P_COMMENT)
            source_uri = str(scheme.get("@id") or "")
        yield {
            "kind": "capability" if group == "GC" else "priority",
            "code": short_code,
            "name": name or names.get(short_code, short_code),
            "description": description,
            "framework": framework,
            "set_code": resolved_set,
            "source_uri": source_uri,
            "attribution": ACARA_ATTRIBUTION,
        }
        # GC/CCP files carry no content descriptions; nothing else to emit.
        return

    # ── Learning-area vocabularies ──────────────────────────────────────────
    for node in graph:
        if not isinstance(node, dict) or not is_statement(node):
            continue

        code = _literal(node, P_STATEMENT_NOTATION, P_NOTATION)
        text = _literal(node, P_DESCRIPTION, P_COMMENT, P_DEFINITION, P_TITLE)
        years = _education_levels(node)
        year_level = years[0] if years else None
        source_uri = str(node.get("@id") or "")

        if _looks_like_achievement_standard(node):
            if not text:
                continue
            yield {
                "kind": "achievement_standard",
                "learning_area": default_area or area_from_code(code) or short_code or "",
                "subject": _literal(node, P_SUBJECT),
                "year_level": year_level if year_level is not None else 0,
                "standard_text": text,
                "framework": framework,
                "set_code": resolved_set,
                "source_uri": source_uri,
                "attribution": ACARA_ATTRIBUTION,
            }
            continue

        if not code:
            # Strand/sub-strand organisers and other unlabelled nodes.
            continue

        # Structural nodes (the vocabulary root, strand/level/subject headings,
        # and MRAC's own changelog entries) carry a statementNotation too, so the
        # `not code` guard above does not exclude them. asn:statementLabel is what
        # actually classifies a node — only curriculum statements become outcomes.
        if _label_of(node).strip().lower() in _ORGANISER_LABELS:
            continue
        if code.strip().lower() in _STRUCTURAL_CODES:
            continue

        match = _ELABORATION_RE.match(code)
        parent_code = match.group("base") if match else None
        ancestors = _ancestor_labels(node, index)
        strand = ancestors[-1] if ancestors else ""
        sub_strand = ancestors[0] if len(ancestors) > 1 else ""

        gc_codes, ccp_codes = _referenced_capabilities(node)

        yield {
            "kind": "outcome",
            "code": code,
            "learning_area": default_area or area_from_code(code) or short_code or "",
            "subject": _literal(node, P_SUBJECT),
            "year_level": year_level if year_level is not None else 0,
            "year_levels": years,
            "strand": strand[:150],
            "sub_strand": sub_strand[:150],
            "content_description": text,
            "is_elaboration": parent_code is not None,
            "parent_code": parent_code,
            "general_capability_codes": gc_codes,
            "cross_curriculum_priority_codes": ccp_codes,
            "framework": framework,
            "set_code": resolved_set,
            "source_uri": source_uri,
            "attribution": ACARA_ATTRIBUTION,
        }


# ── Loader ───────────────────────────────────────────────────────────────────
def _empty_summary(framework: str) -> dict:
    return {
        "set_code": "",
        "source": "",
        "framework": framework,
        "statements_seen": 0,
        "outcomes_created": 0,
        "outcomes_updated": 0,
        "elaborations_linked": 0,
        "capabilities_upserted": 0,
        "priorities_upserted": 0,
        "capability_links": 0,
        "priority_links": 0,
        "standards_upserted": 0,
        "standards_linked": 0,
        "skipped": 0,
        "attribution": ACARA_ATTRIBUTION,
    }


def _get_capability(model, tenant_id, code, framework, names, cache):
    key = (model.__name__, code, framework)
    obj = cache.get(key)
    if obj is None:
        obj, _ = model.objects.get_or_create(
            tenant_id=tenant_id,
            code=code,
            framework=framework,
            defaults={"name": names.get(code, code)},
        )
        cache[key] = obj
    return obj


@transaction.atomic
def load_mrac(
    tenant_id,
    source,
    *,
    set_code: str | None = None,
    framework: str = "ACARA v9",
    link_achievement_standards: bool = True,
    record_run: bool = True,
):
    """
    Idempotently upsert one MRAC export into the tenant's curriculum registry.

    Re-running over the same file UPDATES rows (matched on
    ``tenant_id + code + framework``) and never duplicates. Returns a summary
    dict that includes the ACARA attribution notice.
    """
    summary = _empty_summary(framework)
    source_name = Path(str(source)).name if isinstance(source, (str, Path)) else "<in-memory>"
    summary["source"] = source_name

    records = list(parse_mrac(source, set_code=set_code, framework=framework))
    if records:
        summary["set_code"] = records[0].get("set_code", "") or (set_code or "")
    else:
        summary["set_code"] = set_code or ""

    capability_cache: dict = {}
    standard_cache: dict = {}
    elaboration_parents: dict[str, str] = {}
    outcome_ids: dict[str, object] = {}
    touched_area_years: set[tuple[str, str, int]] = set()

    for record in records:
        kind = record["kind"]

        if kind == "capability":
            obj, _ = GeneralCapability.objects.update_or_create(
                tenant_id=tenant_id,
                code=record["code"],
                framework=framework,
                defaults={
                    "name": record.get("name") or "",
                    "description": record.get("description") or "",
                    "source_uri": (record.get("source_uri") or "")[:500],
                    "is_active": True,
                },
            )
            capability_cache[(GeneralCapability.__name__, record["code"], framework)] = obj
            summary["capabilities_upserted"] += 1
            continue

        if kind == "priority":
            obj, _ = CrossCurriculumPriority.objects.update_or_create(
                tenant_id=tenant_id,
                code=record["code"],
                framework=framework,
                defaults={
                    "name": record.get("name") or "",
                    "description": record.get("description") or "",
                    "source_uri": (record.get("source_uri") or "")[:500],
                    "is_active": True,
                },
            )
            capability_cache[(CrossCurriculumPriority.__name__, record["code"], framework)] = obj
            summary["priorities_upserted"] += 1
            continue

        if kind == "achievement_standard":
            area = record.get("learning_area") or ""
            if not area:
                summary["skipped"] += 1
                continue
            standard, _ = AchievementStandard.objects.update_or_create(
                tenant_id=tenant_id,
                learning_area=area,
                subject=record.get("subject") or "",
                year_level=record.get("year_level") or 0,
                framework=framework,
                defaults={
                    "standard_text": record.get("standard_text") or "",
                    "source_uri": (record.get("source_uri") or "")[:500],
                    "is_active": True,
                },
            )
            standard_cache[(area, record.get("subject") or "", record.get("year_level") or 0)] = standard
            summary["standards_upserted"] += 1
            continue

        # ── kind == "outcome" ───────────────────────────────────────────────
        summary["statements_seen"] += 1
        code = (record.get("code") or "").strip()
        area = (record.get("learning_area") or "").strip()
        if not code or not area:
            summary["skipped"] += 1
            continue

        text = record.get("content_description") or ""
        defaults = {
            "learning_area": area,
            "subject": (record.get("subject") or "")[:100],
            "year_level": record.get("year_level") or 0,
            "strand": (record.get("strand") or "")[:150],
            "sub_strand": (record.get("sub_strand") or "")[:150],
            "content_description": text,
            "is_elaboration": bool(record.get("is_elaboration")),
            "source_uri": (record.get("source_uri") or "")[:500],
            "is_active": True,
        }
        if record.get("is_elaboration"):
            defaults["elaboration"] = text

        outcome, created = CurriculumOutcome.objects.update_or_create(
            tenant_id=tenant_id, code=code, framework=framework, defaults=defaults
        )
        summary["outcomes_created"] += int(created)
        summary["outcomes_updated"] += int(not created)
        outcome_ids[code] = outcome.pk
        touched_area_years.add((area, defaults["subject"], defaults["year_level"]))

        if record.get("parent_code"):
            elaboration_parents[code] = record["parent_code"]

        gc_codes = record.get("general_capability_codes") or []
        if gc_codes:
            objs = [
                _get_capability(
                    GeneralCapability, tenant_id, gc, framework, GENERAL_CAPABILITY_NAMES, capability_cache
                )
                for gc in gc_codes
            ]
            outcome.general_capabilities.set(objs)
            summary["capability_links"] += len(objs)

        ccp_codes = record.get("cross_curriculum_priority_codes") or []
        if ccp_codes:
            objs = [
                _get_capability(
                    CrossCurriculumPriority, tenant_id, ccp, framework,
                    CROSS_CURRICULUM_PRIORITY_NAMES, capability_cache,
                )
                for ccp in ccp_codes
            ]
            outcome.cross_curriculum_priorities.set(objs)
            summary["priority_links"] += len(objs)

    # ── Pass 2: link elaborations to their base content description ─────────
    if elaboration_parents:
        missing = [p for p in set(elaboration_parents.values()) if p not in outcome_ids]
        if missing:
            for row in CurriculumOutcome.objects.filter(
                tenant_id=tenant_id, framework=framework, code__in=missing
            ).values_list("code", "pk"):
                outcome_ids[row[0]] = row[1]
        for child_code, parent_code in elaboration_parents.items():
            parent_pk = outcome_ids.get(parent_code)
            if parent_pk is None or outcome_ids.get(child_code) is None:
                continue
            updated = CurriculumOutcome.objects.filter(pk=outcome_ids[child_code]).update(
                parent_outcome_id=parent_pk
            )
            summary["elaborations_linked"] += updated

    # ── Pass 3: attach the shared achievement standard ──────────────────────
    if link_achievement_standards and touched_area_years:
        for area, subject, year in touched_area_years:
            standard = standard_cache.get((area, subject, year))
            if standard is None:
                standard = AchievementStandard.objects.filter(
                    tenant_id=tenant_id, learning_area=area, year_level=year, framework=framework
                ).first()
            if standard is None:
                continue
            summary["standards_linked"] += CurriculumOutcome.objects.filter(
                tenant_id=tenant_id, framework=framework, learning_area=area, year_level=year
            ).update(achievement_standard_ref=standard)

    if record_run:
        MracImportRun.objects.create(
            tenant_id=tenant_id,
            set_code=summary["set_code"][:20],
            source_name=source_name[:255],
            framework=framework,
            statements_seen=summary["statements_seen"],
            outcomes_created=summary["outcomes_created"],
            outcomes_updated=summary["outcomes_updated"],
            elaborations_linked=summary["elaborations_linked"],
            capability_links=summary["capability_links"],
            priority_links=summary["priority_links"],
            standards_upserted=summary["standards_upserted"],
            skipped=summary["skipped"],
            attribution=ACARA_ATTRIBUTION,
        )

    return summary


def load_mrac_directory(
    tenant_id,
    directory,
    *,
    framework: str = "ACARA v9",
    pattern: str = "*.jsonld",
    record_run: bool = True,
):
    """
    Load every MRAC export in ``directory``. GC/CCP files are processed first so
    capability names/descriptions are already populated when learning-area files
    link to them. Returns ``{"files": [...], "totals": {...}}``.
    """
    root = Path(directory)
    if not root.is_dir():
        raise MracParseError(f"Not a directory: {directory}")

    files = sorted(root.rglob(pattern))

    def _order(path: Path) -> int:
        group, _ = split_set_code(infer_set_code(None, path) or path.stem)
        return 0 if group in ("GC", "CCP") else 1

    files.sort(key=lambda p: (_order(p), str(p)))

    totals = _empty_summary(framework)
    results = []
    for path in files:
        result = load_mrac(tenant_id, path, framework=framework, record_run=record_run)
        results.append(result)
        for key, value in result.items():
            if isinstance(value, int) and key in totals:
                totals[key] += value
    totals["set_code"] = ""
    totals["source"] = str(root)
    return {"files": results, "totals": totals, "attribution": ACARA_ATTRIBUTION}


# ── Optional network fetch (never used by the test suite) ────────────────────
def mrac_url(set_code: str, fmt: str = "jsonld") -> str:
    """
    Canonical export URL for a vocabulary set, e.g.::

        https://vocabulary.curriculum.edu.au/MRAC/2024/04/LA/MAT/export/MRAC/2024/04/LA/MAT.jsonld
    """
    group, code = split_set_code(set_code)
    path = f"{group}/{code}" if group else str(set_code).strip("/").upper()
    suffix = "rdf" if fmt.lower() in ("rdf", "rdfxml", "xml") else "jsonld"
    return f"{MRAC_HOST}/{MRAC_VERSION}/{path}/export/{MRAC_VERSION}/{path}.{suffix}"


def download_set(set_code: str, dest_dir, *, allow_network: bool = False, fmt: str = "jsonld", timeout: int = 120) -> Path:
    """
    Download one MRAC vocabulary set to ``dest_dir``.

    Network access is opt-in: without ``allow_network=True`` this raises, which
    is what keeps the test suite (and any accidental import-time use) offline.
    """
    if not allow_network:
        raise RuntimeError(
            "download_set() requires allow_network=True. MRAC ingestion defaults to "
            "parsing local files; pass --download to the management command to fetch."
        )
    from urllib.request import urlopen  # imported lazily: nothing offline needs it

    group, code = split_set_code(set_code)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    suffix = "rdf" if fmt.lower() in ("rdf", "rdfxml", "xml") else "jsonld"
    target = dest / f"{group or 'SET'}_{code}.{suffix}"
    url = mrac_url(set_code, fmt=fmt)
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - fixed ACARA host
        target.write_bytes(response.read())
    return target
