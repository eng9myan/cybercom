import logging
import time
from typing import Any

import httpx
from django.conf import settings

from platform.terminology.providers.base import TerminologyProvider

logger = logging.getLogger("cybercom.terminology.loinc")

# ---------------------------------------------------------------------------
# Module-level in-memory cache (TTL 1 hour)
# ---------------------------------------------------------------------------
_CACHE_TTL = 3600  # seconds
_search_cache: dict[str, tuple[list[dict[str, Any]], float]] = {}

LOINC_FHIR_EXPAND_URL = "https://loinc.org/fhir/ValueSet/$expand"


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


class LOINCProvider(TerminologyProvider):
    """
    Terminology provider for LOINC (Logical Observation Identifiers Names and Codes).
    Supports laboratory measurements, clinical observations, and mappings to other standards.

    Live search uses the NLM LOINC FHIR API (https://loinc.org/fhir/ValueSet/$expand).
    No authentication required for basic queries.
    Falls back to hardcoded observations on any network or API failure.
    """

    # ------------------------------------------------------------------
    # Fallback / seed data
    # ------------------------------------------------------------------
    OBSERVATIONS = {
        "2339-0": {
            "display": "Glucose [Mass/volume] in Blood",
            "class": "CHEM",
            "system": "Bld",
            "scale": "Qn",
            "definition": "Quantitative measurement of glucose mass concentration in blood.",
            "synonyms": ["Blood Glucose", "GLU", "Blood Sugar"],
            "mappings": {"snomed": "365812005"},
        },
        "4544-3": {
            "display": "Hemoglobin A1c [Fraction] in Blood",
            "class": "HEM/BC",
            "system": "Bld",
            "scale": "Qn",
            "definition": "Quantitative measurement of HbA1c fraction in blood.",
            "synonyms": ["HbA1c", "Glycated hemoglobin", "Glycohemoglobin", "A1c"],
            "mappings": {"snomed": "365825000"},
        },
        "29463-7": {
            "display": "Body weight",
            "class": "CLIN",
            "system": "Patient",
            "scale": "Qn",
            "definition": "Quantitative measurement of patient body weight.",
            "synonyms": ["Weight", "Body mass", "Wt"],
            "mappings": {"snomed": "27113001"},
        },
        "8867-4": {
            "display": "Heart rate",
            "class": "CLIN",
            "system": "Pt",
            "scale": "Qn",
            "definition": "Heart rate measured in beats per minute.",
            "synonyms": ["Pulse", "Heart beats", "HR"],
            "mappings": {"snomed": "364075005"},
        },
    }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _search_mock(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fallback search over hardcoded OBSERVATIONS."""
        results: list[dict[str, Any]] = []
        q = query.lower()
        for code, details in self.OBSERVATIONS.items():
            matches_synonym = any(q in s.lower() for s in details["synonyms"])
            if (
                q in code.lower()
                or q in details["display"].lower()
                or q in details["definition"].lower()
                or matches_synonym
            ):
                results.append({"code": code, "display": details["display"], "type": "observation"})
                if len(results) >= limit:
                    return results
        return results

    # ------------------------------------------------------------------
    # TerminologyProvider interface
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10, **kwargs) -> list[dict[str, Any]]:
        """
        Search LOINC codes via the NLM FHIR ValueSet $expand endpoint (public, no auth).
        Falls back to hardcoded data on failure.
        """
        cache_key = f"loinc_search|{query}|{limit}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            params: dict[str, Any] = {
                "filter": query,
                "count": limit,
            }
            headers = {"Accept": "application/fhir+json"}
            with httpx.Client(timeout=_get_timeout()) as client:
                response = client.get(LOINC_FHIR_EXPAND_URL, headers=headers, params=params)

            if response.status_code != 200:
                logger.warning(
                    "LOINC FHIR API returned HTTP %d for query '%s' — falling back to mock data",
                    response.status_code,
                    query,
                )
                return self._search_mock(query, limit)

            data = response.json()
            expansion = data.get("expansion", {})
            results: list[dict[str, Any]] = []
            for item in expansion.get("contains", [])[:limit]:
                code = item.get("code", "")
                display = item.get("display", "")
                if code and display:
                    results.append(
                        {
                            "code": code,
                            "display": display,
                            "type": "observation",
                            "system": item.get("system", "http://loinc.org"),
                        }
                    )

            _cache_set(cache_key, results)
            return results

        except Exception as exc:
            logger.warning(
                "LOINC FHIR API call failed for query '%s': %s — falling back to mock data",
                query,
                exc,
            )
            return self._search_mock(query, limit)

    def lookup(self, code: str, **kwargs) -> dict[str, Any] | None:
        if code in self.OBSERVATIONS:
            details = self.OBSERVATIONS[code]
            return {
                "code": code,
                "display": details["display"],
                "class": details["class"],
                "system": details["system"],
                "scale": details["scale"],
                "definition": details["definition"],
            }
        return None

    def validate(self, code: str, **kwargs) -> bool:
        return code in self.OBSERVATIONS

    def translate(self, code: str, target_system: str, **kwargs) -> dict[str, Any] | None:
        target_system = target_system.lower()
        if code in self.OBSERVATIONS:
            mappings = self.OBSERVATIONS[code]["mappings"]
            if target_system in mappings:
                return {
                    "code": mappings[target_system],
                    "system": target_system.upper(),
                    "relationship": "equivalent",
                }
        return None

    def expand(
        self, value_set: str, filter_str: str | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        results = []
        if "vital" in value_set.lower():
            for code in ["8867-4", "29463-7"]:
                results.append({"code": code, "display": self.OBSERVATIONS[code]["display"]})
        elif "chemistry" in value_set.lower() or "lab" in value_set.lower():
            for code in ["2339-0", "4544-3"]:
                results.append({"code": code, "display": self.OBSERVATIONS[code]["display"]})
        else:
            for code, details in self.OBSERVATIONS.items():
                results.append({"code": code, "display": details["display"]})

        if filter_str:
            f = filter_str.lower()
            results = [r for r in results if f in r["code"].lower() or f in r["display"].lower()]
        return results

    def get_children(self, code: str, **kwargs) -> list[dict[str, Any]]:
        # LOINC uses a flat (part-based) hierarchy not expressed in this provider
        return []

    def get_parents(self, code: str, **kwargs) -> list[dict[str, Any]]:
        if code in self.OBSERVATIONS:
            category = self.OBSERVATIONS[code]["class"]
            return [{"code": category, "display": f"LOINC Class {category}"}]
        return []

    def get_synonyms(self, code: str, **kwargs) -> list[str]:
        if code in self.OBSERVATIONS:
            return self.OBSERVATIONS[code]["synonyms"]
        return []

    def get_mappings(self, code: str, target_system: str, **kwargs) -> list[dict[str, Any]]:
        translated = self.translate(code, target_system)
        return [translated] if translated else []

    def get_version(self) -> str:
        return "2.77"
