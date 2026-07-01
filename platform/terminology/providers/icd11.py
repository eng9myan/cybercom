import logging
import re
import time
from typing import Any

import httpx
from django.conf import settings

from platform.terminology.providers.base import TerminologyProvider

logger = logging.getLogger("cybercom.terminology.icd11")

# ---------------------------------------------------------------------------
# Module-level in-memory cache (TTL 1 hour)
# ---------------------------------------------------------------------------
_CACHE_TTL = 3600  # seconds
_search_cache: dict[str, tuple[list[dict[str, Any]], float]] = {}

ICD11_SEARCH_URL = "https://id.who.int/icd/entity/search"


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


class ICD11Provider(TerminologyProvider):
    """
    Terminology provider for WHO ICD-11 (MMS).
    Supports stem codes, extension codes, post-coordination parsing, and ICD-10 crosswalks.

    Live search uses the WHO ICD-11 REST API (https://id.who.int/icd/entity/search).
    Requires ICD11_API_TOKEN in settings (obtained from https://icdaccessmanagement.who.int/).
    Falls back to hardcoded codes when the token is absent or any API call fails.
    """

    # ------------------------------------------------------------------
    # Fallback / seed data (used when token absent or API unavailable)
    # ------------------------------------------------------------------
    STEM_CODES = {
        "1B10.0": {
            "display": "Type 1 diabetes mellitus",
            "definition": "A form of diabetes characterized by autoimmune destruction of pancreatic beta cells.",
            "parents": ["1B10"],
            "children": [],
        },
        "1B10.1": {
            "display": "Type 2 diabetes mellitus",
            "definition": "A form of diabetes characterized by insulin resistance and relative insulin deficiency.",
            "parents": ["1B10"],
            "children": [],
        },
        "FA80": {
            "display": "Osteoarthritis of hip",
            "definition": "Degenerative joint disease of the hip joint.",
            "parents": ["FA8"],
            "children": ["FA80.0", "FA80.1"],
        },
        "FA81": {
            "display": "Osteoarthritis of knee",
            "definition": "Degenerative joint disease of the knee joint.",
            "parents": ["FA8"],
            "children": ["FA81.0", "FA81.1"],
        },
        "CA00": {
            "display": "Acute nasopharyngitis [common cold]",
            "definition": "Acute viral infection of the upper respiratory tract.",
            "parents": ["CA0"],
            "children": [],
        },
    }

    EXTENSION_CODES = {
        "XS17": {"display": "Present on admission", "type": "diagnosis_timing"},
        "XS18": {"display": "Developed after admission", "type": "diagnosis_timing"},
        "XY0Y": {"display": "Left side", "type": "lateralities"},
        "XY1Y": {"display": "Right side", "type": "lateralities"},
    }

    ICD10_CROSSWALK = {
        "E10": "1B10.0",
        "E11": "1B10.1",
        "M16": "FA80",
        "M17": "FA81",
        "J00": "CA00",
    }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _search_mock(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Fallback search over hardcoded STEM_CODES and EXTENSION_CODES."""
        results: list[dict[str, Any]] = []
        q = query.lower()

        for code, details in self.STEM_CODES.items():
            if (
                q in code.lower()
                or q in details["display"].lower()
                or q in details["definition"].lower()
            ):
                results.append({"code": code, "display": details["display"], "type": "stem"})
                if len(results) >= limit:
                    return results

        for code, details in self.EXTENSION_CODES.items():
            if q in code.lower() or q in details["display"].lower():
                results.append({"code": code, "display": details["display"], "type": "extension"})
                if len(results) >= limit:
                    return results

        return results

    # ------------------------------------------------------------------
    # TerminologyProvider interface
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10, **kwargs) -> list[dict[str, Any]]:
        """
        Search ICD-11 concepts.  Calls the WHO REST API when ICD11_API_TOKEN is set;
        otherwise falls back to hardcoded codes with a warning.
        """
        token: str = getattr(settings, "ICD11_API_TOKEN", "")

        if not token:
            logger.warning(
                "ICD11_API_TOKEN is not configured — using fallback hardcoded codes for ICD-11 search"
            )
            return self._search_mock(query, limit)

        cache_key = f"icd11_search|{query}|{limit}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Accept-Language": "en",
                "API-Version": "v2",
            }
            params: dict[str, str] = {
                "q": query,
                "subtreeFilterUsage": "foundationDescendant",
            }
            with httpx.Client(timeout=_get_timeout()) as client:
                response = client.get(ICD11_SEARCH_URL, headers=headers, params=params)

            if response.status_code != 200:
                logger.warning(
                    "ICD-11 API returned HTTP %d for query '%s' — falling back to mock data",
                    response.status_code,
                    query,
                )
                return self._search_mock(query, limit)

            data = response.json()
            results: list[dict[str, Any]] = []
            for entity in data.get("destinationEntities", [])[:limit]:
                code = entity.get("theCode", "")
                title = entity.get("title", "")
                if not code or not title:
                    continue
                results.append(
                    {
                        "code": code,
                        "display": title,
                        "type": "stem",
                        "id": entity.get("id", ""),
                    }
                )

            _cache_set(cache_key, results)
            return results

        except Exception as exc:
            logger.warning(
                "ICD-11 API call failed for query '%s': %s — falling back to mock data",
                query,
                exc,
            )
            return self._search_mock(query, limit)

    def lookup(self, code: str, **kwargs) -> dict[str, Any] | None:
        # Handle post-coordinated cluster (e.g. FA81&XY1Y&XS17)
        if "&" in code or "/" in code:
            parts = re.split(r"[&/]", code)
            stem_code = parts[0]
            extensions = parts[1:]

            if stem_code not in self.STEM_CODES:
                return None

            stem_details = self.STEM_CODES[stem_code]
            display_parts = [stem_details["display"]]
            extension_details = []

            for ext in extensions:
                if ext in self.EXTENSION_CODES:
                    ext_info = self.EXTENSION_CODES[ext]
                    display_parts.append(ext_info["display"])
                    extension_details.append({"code": ext, **ext_info})

            return {
                "code": code,
                "display": ", ".join(display_parts),
                "is_post_coordinated": True,
                "stem_code": stem_code,
                "extensions": extension_details,
                "definition": stem_details["definition"],
            }

        # Single code lookup (uses fallback data; WHO entity URI lookup would need separate mapping)
        if code in self.STEM_CODES:
            details = self.STEM_CODES[code]
            return {
                "code": code,
                "display": details["display"],
                "is_post_coordinated": False,
                "definition": details["definition"],
            }
        elif code in self.EXTENSION_CODES:
            details = self.EXTENSION_CODES[code]
            return {
                "code": code,
                "display": details["display"],
                "is_post_coordinated": False,
                "definition": f"ICD-11 Extension code for {details['type']}.",
            }
        return None

    def validate(self, code: str, **kwargs) -> bool:
        if not code:
            return False
        parts = re.split(r"[&/]", code)
        stem = parts[0]
        if stem not in self.STEM_CODES:
            return False
        for ext in parts[1:]:
            if ext not in self.EXTENSION_CODES:
                return False
        return True

    def translate(self, code: str, target_system: str, **kwargs) -> dict[str, Any] | None:
        target_system = target_system.lower()
        if target_system in ("icd10", "icd-10"):
            for icd10, icd11 in self.ICD10_CROSSWALK.items():
                if icd11 == code:
                    return {"code": icd10, "system": "ICD-10", "relationship": "equivalent"}
        elif target_system in ("icd11", "icd-11"):
            if code in self.ICD10_CROSSWALK:
                icd11_code = self.ICD10_CROSSWALK[code]
                display = self.STEM_CODES[icd11_code]["display"]
                return {
                    "code": icd11_code,
                    "display": display,
                    "system": "ICD-11",
                    "relationship": "equivalent",
                }
        return None

    def expand(
        self, value_set: str, filter_str: str | None = None, **kwargs
    ) -> list[dict[str, Any]]:
        results = []
        if "diabetes" in value_set.lower():
            for code in ["1B10.0", "1B10.1"]:
                details = self.STEM_CODES[code]
                results.append({"code": code, "display": details["display"]})
        elif "osteoarthritis" in value_set.lower():
            for code in ["FA80", "FA81"]:
                details = self.STEM_CODES[code]
                results.append({"code": code, "display": details["display"]})
        else:
            for code, details in self.STEM_CODES.items():
                results.append({"code": code, "display": details["display"]})

        if filter_str:
            f = filter_str.lower()
            results = [r for r in results if f in r["code"].lower() or f in r["display"].lower()]
        return results

    def get_children(self, code: str, **kwargs) -> list[dict[str, Any]]:
        if code in self.STEM_CODES:
            children_codes = self.STEM_CODES[code].get("children", [])
            return [
                {"code": c, "display": f"Subtype of {self.STEM_CODES[code]['display']}"}
                for c in children_codes
            ]
        return []

    def get_parents(self, code: str, **kwargs) -> list[dict[str, Any]]:
        if code in self.STEM_CODES:
            parent_codes = self.STEM_CODES[code].get("parents", [])
            return [{"code": p, "display": f"Parent category {p}"} for p in parent_codes]
        return []

    def get_synonyms(self, code: str, **kwargs) -> list[str]:
        synonyms = {
            "1B10.0": ["Type 1 Diabetes", "IDDM", "Juvenile onset diabetes"],
            "1B10.1": ["Type 2 Diabetes", "NIDDM", "Adult-onset diabetes"],
            "FA80": ["Hip osteoarthritis", "Coxarthrosis"],
            "FA81": ["Knee osteoarthritis", "Gonarthrosis"],
        }
        return synonyms.get(code, [])

    def get_mappings(self, code: str, target_system: str, **kwargs) -> list[dict[str, Any]]:
        translated = self.translate(code, target_system)
        return [translated] if translated else []

    def get_version(self) -> str:
        return "2025.1.0-icd11"
