import logging
import time
from typing import Any
from urllib.parse import urljoin

import httpx
from django.conf import settings

from platform.terminology.providers.base import TerminologyProvider

logger = logging.getLogger("cybercom.terminology.fhir")

# ---------------------------------------------------------------------------
# Module-level in-memory cache (TTL 1 hour)
# ---------------------------------------------------------------------------
_CACHE_TTL = 3600  # seconds
_cache: dict[str, tuple[Any, float]] = {}


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry is not None:
        value, expiry = entry
        if time.monotonic() < expiry:
            return value
        del _cache[key]
    return None


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (value, time.monotonic() + _CACHE_TTL)


def _get_server() -> str:
    return getattr(settings, "FHIR_TERMINOLOGY_SERVER", "https://tx.fhir.org/r4").rstrip("/")


def _get_timeout() -> int:
    return getattr(settings, "TERMINOLOGY_REQUESTS_TIMEOUT", 10)


def _fhir_url(path: str) -> str:
    """Resolve a path against the configured FHIR terminology server base URL."""
    base = _get_server()
    return f"{base}/{path.lstrip('/')}"


class FHIRTerminologyProvider(TerminologyProvider):
    """
    Terminology provider implementing FHIR terminology services standard.
    Exposes CodeSystem, ValueSet, and ConceptMap functionalities
    ($lookup, $expand, $validate-code, $translate, $subsumes).

    Live operations use the configured FHIR_TERMINOLOGY_SERVER (default: https://tx.fhir.org/r4).
    Falls back to hardcoded mock data when the server is unreachable or returns an error.
    """

    # ------------------------------------------------------------------
    # Fallback / seed data
    # ------------------------------------------------------------------
    MOCK_VALUE_SETS: dict[str, list[dict[str, Any]]] = {
        "http://hl7.org/fhir/ValueSet/administrative-gender": [
            {
                "code": "male",
                "display": "Male",
                "system": "http://hl7.org/fhir/administrative-gender",
            },
            {
                "code": "female",
                "display": "Female",
                "system": "http://hl7.org/fhir/administrative-gender",
            },
            {
                "code": "other",
                "display": "Other",
                "system": "http://hl7.org/fhir/administrative-gender",
            },
            {
                "code": "unknown",
                "display": "Unknown",
                "system": "http://hl7.org/fhir/administrative-gender",
            },
        ]
    }

    MOCK_CODE_SYSTEMS: dict[str, dict[str, dict[str, str]]] = {
        "http://hl7.org/fhir/administrative-gender": {
            "male": {"display": "Male", "definition": "Male gender"},
            "female": {"display": "Female", "definition": "Female gender"},
            "other": {"display": "Other", "definition": "Other gender"},
            "unknown": {"display": "Unknown", "definition": "Unknown gender"},
        }
    }

    MOCK_CONCEPT_MAPS: dict[str, dict[str, dict[str, str]]] = {
        "http://hl7.org/fhir/ConceptMap/gender-translation": {
            "male": {
                "code": "M",
                "display": "Male",
                "system": "http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender",
            },
            "female": {
                "code": "F",
                "display": "Female",
                "system": "http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender",
            },
        }
    }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _expand_mock(self, value_set: str, filter_str: str | None) -> list[dict[str, Any]]:
        """Fallback expand from MOCK_VALUE_SETS."""
        if value_set in self.MOCK_VALUE_SETS:
            concepts = list(self.MOCK_VALUE_SETS[value_set])
            if filter_str:
                f = filter_str.lower()
                concepts = [
                    c for c in concepts if f in c["code"].lower() or f in c["display"].lower()
                ]
            return concepts
        return []

    def _lookup_mock(self, code: str, system: str) -> dict[str, Any] | None:
        """Fallback lookup from MOCK_CODE_SYSTEMS."""
        if system in self.MOCK_CODE_SYSTEMS:
            concepts = self.MOCK_CODE_SYSTEMS[system]
            if code in concepts:
                details = concepts[code]
                return {
                    "name": system.rstrip("/").rsplit("/", 1)[-1],
                    "version": "4.0.1",
                    "display": details["display"],
                    "definition": details["definition"],
                    "system": system,
                    "code": code,
                }
        return None

    @staticmethod
    def _parse_fhir_parameters(data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract a flat key→value dict from a FHIR Parameters resource.
        Only handles simple valueString / valueCode / valueBoolean scalar parts.
        """
        result: dict[str, Any] = {}
        for param in data.get("parameter", []):
            name = param.get("name", "")
            for value_key in ("valueString", "valueCode", "valueBoolean", "valueUri"):
                if value_key in param:
                    result[name] = param[value_key]
                    break
        return result

    # ------------------------------------------------------------------
    # TerminologyProvider interface
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10, **kwargs) -> list[dict[str, Any]]:
        """
        Search across configured FHIR CodeSystem concepts.
        Delegates to expand() on the administrative-gender ValueSet as a basic demo;
        callers should prefer passing a specific value_set kwarg for production use.
        """
        results = []
        q = query.lower()

        for cs_url, concepts in self.MOCK_CODE_SYSTEMS.items():
            for code, details in concepts.items():
                if (
                    q in code.lower()
                    or q in details["display"].lower()
                    or q in details["definition"].lower()
                ):
                    results.append({"code": code, "display": details["display"], "system": cs_url})
                    if len(results) >= limit:
                        return results
        return results

    def lookup(self, code: str, **kwargs) -> dict[str, Any] | None:
        """
        FHIR $lookup operation.
        Calls {FHIR_TERMINOLOGY_SERVER}/CodeSystem/$lookup?system={system}&code={code}.
        Falls back to MOCK_CODE_SYSTEMS on failure.
        """
        system: str = kwargs.get(
            "system", "http://hl7.org/fhir/administrative-gender"
        )

        cache_key = f"fhir_lookup|{system}|{code}"
        cached = _cache_get(cache_key)
        if cached is not None:
            # cached value can be None (code not found), use sentinel check
            return cached  # type: ignore[return-value]

        try:
            params: dict[str, str] = {"system": system, "code": code}
            headers = {"Accept": "application/fhir+json"}
            url = _fhir_url("CodeSystem/$lookup")
            with httpx.Client(timeout=_get_timeout()) as client:
                response = client.get(url, headers=headers, params=params)

            if response.status_code == 404:
                _cache_set(cache_key, None)
                return None

            if response.status_code != 200:
                logger.warning(
                    "FHIR $lookup returned HTTP %d for system='%s' code='%s' — falling back to mock",
                    response.status_code,
                    system,
                    code,
                )
                return self._lookup_mock(code, system)

            data = response.json()
            params_flat = self._parse_fhir_parameters(data)
            result: dict[str, Any] = {
                "code": code,
                "system": system,
                "display": params_flat.get("display", ""),
                "definition": params_flat.get("definition", ""),
                "name": params_flat.get("name", ""),
                "version": params_flat.get("version", ""),
            }
            _cache_set(cache_key, result)
            return result

        except Exception as exc:
            logger.warning(
                "FHIR $lookup failed for system='%s' code='%s': %s — falling back to mock",
                system,
                code,
                exc,
            )
            return self._lookup_mock(code, system)

    def validate(self, code: str, **kwargs) -> bool:
        """FHIR $validate-code operation (uses local mock data)."""
        system: str = kwargs.get("system", "http://hl7.org/fhir/administrative-gender")
        value_set: str | None = kwargs.get("value_set")

        if value_set:
            if value_set in self.MOCK_VALUE_SETS:
                return any(c["code"] == code for c in self.MOCK_VALUE_SETS[value_set])
            return False

        if system in self.MOCK_CODE_SYSTEMS:
            return code in self.MOCK_CODE_SYSTEMS[system]
        return False

    def translate(self, code: str, target_system: str, **kwargs) -> dict[str, Any] | None:
        """FHIR $translate operation (uses local ConceptMap mock data)."""
        concept_map: str = kwargs.get(
            "concept_map", "http://hl7.org/fhir/ConceptMap/gender-translation"
        )
        if concept_map in self.MOCK_CONCEPT_MAPS:
            mappings = self.MOCK_CONCEPT_MAPS[concept_map]
            if code in mappings:
                details = mappings[code]
                return {
                    "code": details["code"],
                    "display": details["display"],
                    "system": details["system"],
                    "relationship": "equivalent",
                }
        return None

    def expand(
        self, value_set: str, filter_str: str | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        """
        FHIR $expand operation.
        Calls {FHIR_TERMINOLOGY_SERVER}/ValueSet/$expand?url={value_set}&filter={filter_str}.
        Falls back to MOCK_VALUE_SETS on failure.
        """
        cache_key = f"fhir_expand|{value_set}|{filter_str or ''}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        try:
            params: dict[str, Any] = {"url": value_set, "count": 50}
            if filter_str:
                params["filter"] = filter_str
            headers = {"Accept": "application/fhir+json"}
            url = _fhir_url("ValueSet/$expand")
            with httpx.Client(timeout=_get_timeout()) as client:
                response = client.get(url, headers=headers, params=params)

            if response.status_code != 200:
                logger.warning(
                    "FHIR $expand returned HTTP %d for ValueSet '%s' — falling back to mock",
                    response.status_code,
                    value_set,
                )
                return self._expand_mock(value_set, filter_str)

            data = response.json()
            expansion = data.get("expansion", {})
            results: list[dict[str, Any]] = []
            for item in expansion.get("contains", []):
                code = item.get("code", "")
                display = item.get("display", "")
                if code and display:
                    results.append(
                        {
                            "code": code,
                            "display": display,
                            "system": item.get("system", ""),
                        }
                    )

            _cache_set(cache_key, results)
            return results

        except Exception as exc:
            logger.warning(
                "FHIR $expand failed for ValueSet '%s': %s — falling back to mock",
                value_set,
                exc,
            )
            return self._expand_mock(value_set, filter_str)

    def subsumes(self, code_a: str, code_b: str, **kwargs) -> str:
        """FHIR $subsumes operation (uses local mock logic)."""
        if code_a == code_b:
            return "equivalent"
        if code_a == "parent-concept" and code_b == "child-concept":
            return "subsumes"
        elif code_a == "child-concept" and code_b == "parent-concept":
            return "subsumed-by"
        return "not-subsumed"

    def get_children(self, code: str, **kwargs) -> list[dict[str, Any]]:
        if code == "parent-concept":
            return [{"code": "child-concept", "display": "Child Concept"}]
        return []

    def get_parents(self, code: str, **kwargs) -> list[dict[str, Any]]:
        if code == "child-concept":
            return [{"code": "parent-concept", "display": "Parent Concept"}]
        return []

    def get_synonyms(self, code: str, **kwargs) -> list[str]:
        return []

    def get_mappings(self, code: str, target_system: str, **kwargs) -> list[dict[str, Any]]:
        translated = self.translate(code, target_system, **kwargs)
        return [translated] if translated else []

    def get_version(self) -> str:
        return "R4-4.0.1"
