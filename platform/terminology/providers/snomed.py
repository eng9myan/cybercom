import logging
import time
from typing import Any

import httpx
from django.conf import settings

from platform.terminology.providers.base import TerminologyProvider

logger = logging.getLogger("cybercom.terminology.snomed")

# ---------------------------------------------------------------------------
# Module-level in-memory cache (TTL 1 hour)
# ---------------------------------------------------------------------------
_CACHE_TTL = 3600  # seconds
_search_cache: dict[str, tuple[list[dict[str, Any]], float]] = {}

SNOWSTORM_BASE_URL = "https://browser.ihtsdotools.org/snowstorm/snomed-ct"
SNOWSTORM_CONCEPTS_URL = f"{SNOWSTORM_BASE_URL}/MAIN/concepts"


def _cache_get(key: str) -> list[dict[str, Any]] | None:
    entry = _search_cache.get(key)
    if entry is not None:
        value, expiry = entry
        if time.monotonic() < expiry:
            return value
        del _search_cache[key]
    return None


def _cache_set(key: str, value: list[dict[str, Any]]) -> None:
    _search_cache[key] = (value, time.monotonic() + _CACHE_TTL)


def _get_timeout() -> int:
    return getattr(settings, "TERMINOLOGY_REQUESTS_TIMEOUT", 10)


class SNOMEDProvider(TerminologyProvider):
    """
    Terminology provider for SNOMED CT (Systematized Nomenclature of Medicine Clinical Terms).
    Supports clinical concepts, synonyms, hierarchies, and ICD-11 mappings.

    Live search uses the SNOMED International Snowstorm Browser API (public, no auth required).
    Falls back to hardcoded concepts on any network or API failure.
    """

    # ------------------------------------------------------------------
    # Fallback / seed data
    # ------------------------------------------------------------------
    CONCEPTS = {
        "111553001": {
            "display": "Type 1 diabetes mellitus (disorder)",
            "definition": "A type 1 diabetes mellitus disorder characterized by autoimmune destruction of beta cells.",
            "parents": ["73211009"],
            "children": [],
            "synonyms": [
                "Type 1 diabetes",
                "Juvenile onset diabetes mellitus",
                "Autoimmune diabetes",
            ],
            "relationships": {"finding_site": "113331007", "associated_morphology": "56200009"},
        },
        "44054006": {
            "display": "Type 2 diabetes mellitus (disorder)",
            "definition": "A type 2 diabetes mellitus disorder characterized by resistance to insulin action.",
            "parents": ["73211009"],
            "children": [],
            "synonyms": ["Type 2 diabetes", "NIDDM", "Adult-onset diabetes mellitus"],
            "relationships": {"finding_site": "113331007", "associated_morphology": "56200009"},
        },
        "239720000": {
            "display": "Osteoarthritis of hip (disorder)",
            "definition": "Degenerative joint disease affecting the hip joint.",
            "parents": ["394659003"],
            "children": [],
            "synonyms": ["Coxarthrosis", "Degenerative arthritis of hip"],
            "relationships": {"finding_site": "24184005"},
        },
        "371038006": {
            "display": "Osteoarthritis of knee (disorder)",
            "definition": "Degenerative joint disease affecting the knee joint.",
            "parents": ["394659003"],
            "children": [],
            "synonyms": ["Gonarthrosis", "Degenerative arthritis of knee"],
            "relationships": {"finding_site": "45271004"},
        },
        "73211009": {
            "display": "Diabetes mellitus (disorder)",
            "definition": "A metabolic disorder characterized by chronic hyperglycemia.",
            "parents": ["138875005"],
            "children": ["111553001", "44054006"],
            "synonyms": ["Sugar diabetes", "Diabetes"],
            "relationships": {},
        },
    }

    SNOMED_TO_ICD11 = {
        "111553001": "1B10.0",
        "44054006": "1B10.1",
        "239720000": "FA80",
        "371038006": "FA81",
    }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _search_mock(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fallback search over hardcoded CONCEPTS."""
        results: list[dict[str, Any]] = []
        q = query.lower()
        for code, details in self.CONCEPTS.items():
            matches_synonym = any(q in s.lower() for s in details["synonyms"])
            if (
                q in code.lower()
                or q in details["display"].lower()
                or q in details["definition"].lower()
                or matches_synonym
            ):
                results.append({"code": code, "display": details["display"], "type": "concept"})
                if len(results) >= limit:
                    return results
        return results

    # ------------------------------------------------------------------
    # TerminologyProvider interface
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10, **kwargs) -> list[dict[str, Any]]:
        """
        Search SNOMED CT concepts via the Snowstorm Browser API (public, no auth).
        Falls back to hardcoded data on failure.
        """
        cache_key = f"snomed_search|{query}|{limit}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            params: dict[str, Any] = {
                "term": query,
                "activeFilter": "true",
                "limit": limit,
            }
            headers = {"Accept": "application/json"}
            with httpx.Client(timeout=_get_timeout()) as client:
                response = client.get(SNOWSTORM_CONCEPTS_URL, headers=headers, params=params)

            if response.status_code != 200:
                logger.warning(
                    "SNOMED Snowstorm API returned HTTP %d for query '%s' — falling back to mock data",
                    response.status_code,
                    query,
                )
                return self._search_mock(query, limit)

            data = response.json()
            results: list[dict[str, Any]] = []
            for item in data.get("items", [])[:limit]:
                concept_id = item.get("conceptId", "")
                # Preferred term lives under pt.term; fsn.term is the fully-specified name
                pt = item.get("pt") or {}
                display = pt.get("term") or item.get("fsn", {}).get("term", "")
                if concept_id and display:
                    results.append(
                        {
                            "code": concept_id,
                            "display": display,
                            "type": "concept",
                            "active": item.get("active", True),
                        }
                    )

            _cache_set(cache_key, results)
            return results

        except Exception as exc:
            logger.warning(
                "SNOMED Snowstorm API call failed for query '%s': %s — falling back to mock data",
                query,
                exc,
            )
            return self._search_mock(query, limit)

    def lookup(self, code: str, **kwargs) -> dict[str, Any] | None:
        if code in self.CONCEPTS:
            details = self.CONCEPTS[code]
            return {
                "code": code,
                "display": details["display"],
                "definition": details["definition"],
                "relationships": details["relationships"],
            }
        return None

    def validate(self, code: str, **kwargs) -> bool:
        return code in self.CONCEPTS

    def translate(self, code: str, target_system: str, **kwargs) -> dict[str, Any] | None:
        target_system = target_system.lower()
        if target_system in ("icd11", "icd-11"):
            if code in self.SNOMED_TO_ICD11:
                icd11_code = self.SNOMED_TO_ICD11[code]
                return {"code": icd11_code, "system": "ICD-11", "relationship": "equivalent"}
        return None

    def expand(
        self, value_set: str, filter_str: str | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        results = []
        if "diabetes" in value_set.lower():
            for code in ["111553001", "44054006"]:
                results.append({"code": code, "display": self.CONCEPTS[code]["display"]})
        else:
            for code, details in self.CONCEPTS.items():
                results.append({"code": code, "display": details["display"]})

        if filter_str:
            f = filter_str.lower()
            results = [r for r in results if f in r["code"].lower() or f in r["display"].lower()]
        return results

    def get_children(self, code: str, **kwargs) -> list[dict[str, Any]]:
        if code in self.CONCEPTS:
            children = self.CONCEPTS[code].get("children", [])
            return [{"code": c, "display": self.CONCEPTS[c]["display"]} for c in children]
        return []

    def get_parents(self, code: str, **kwargs) -> list[dict[str, Any]]:
        if code in self.CONCEPTS:
            parents = self.CONCEPTS[code].get("parents", [])
            return [
                {"code": p, "display": self.CONCEPTS.get(p, {}).get("display", f"Parent {p}")}
                for p in parents
            ]
        return []

    def get_synonyms(self, code: str, **kwargs) -> list[str]:
        if code in self.CONCEPTS:
            return self.CONCEPTS[code].get("synonyms", [])
        return []

    def get_mappings(self, code: str, target_system: str, **kwargs) -> list[dict[str, Any]]:
        translated = self.translate(code, target_system)
        return [translated] if translated else []

    def get_version(self) -> str:
        return "2025.01.31-snomed"
