"""
Real WHO ICD-11 API client.

WHO's ICD-API is documented at https://icd.who.int/icdapi and requires
free registration at https://icdaccessmanagement.who.int/ to obtain a
Client ID + Secret. Access is granted through OAuth2 client_credentials
(NOT a static bearer token) — the exchanged access token is short-lived
(~3600s in prod) and MUST be refreshed. This client caches it via
:mod:`django.core.cache` for 55 minutes (5 min safety margin) so a
process-restart or a second worker doesn't have to re-exchange on every
call.

All HTTP calls go through :mod:`httpx`. Every I/O method takes an
optional injectable ``client`` argument to make it trivial to unit-test
without opening a real socket.

The public surface intentionally mirrors the WHO ICD-11 API's own
concepts:

* :meth:`WHOICDClient.search`        — linearization search
  (``GET /icd/release/11/{release}/mms/search``)
* :meth:`WHOICDClient.entity`        — foundation entity by id
  (``GET /icd/entity/{entity_id}``)
* :meth:`WHOICDClient.linearization` — linearization entity by code
  (``GET /icd/release/11/{release}/mms/{code}``)
* :meth:`WHOICDClient.foundation`    — resolve a full foundation URI
* :meth:`WHOICDClient.code_info`     — code metadata
  (``GET /icd/release/11/{release}/mms/codeinfo/{code}``)

Configuration (all env vars):

    WHO_ICD_CLIENT_ID       (required for real calls)
    WHO_ICD_CLIENT_SECRET   (required for real calls)
    WHO_ICD_RELEASE         (default: "2024-01")
    WHO_ICD_BASE_URL        (default: "https://id.who.int/icd")
    WHO_ICD_TOKEN_URL       (default: "https://icdaccessmanagement.who.int/connect/token")
    WHO_ICD_SCOPE           (default: "icdapi_access")
    WHO_ICD_TIMEOUT         (default: "30", seconds)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional
from urllib.parse import quote

import httpx
from django.core.cache import cache

logger = logging.getLogger("products.cymed.integrations.whoicd")


# ---------------------------------------------------------------------------
# Endpoints & defaults
# ---------------------------------------------------------------------------
DEFAULT_TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"
DEFAULT_BASE_URL = "https://id.who.int/icd"
DEFAULT_RELEASE = "2024-01"
DEFAULT_SCOPE = "icdapi_access"
DEFAULT_TIMEOUT = 30.0

# django.core.cache key + TTL: token real lifetime is ~3600s; refresh a bit
# before that so a race between two workers doesn't blow up on an expired
# token 500ms before the cache TTL would have naturally kicked in.
_TOKEN_CACHE_KEY = "cymed:whoicd:oauth_token"
_TOKEN_CACHE_TTL = 55 * 60  # 55 minutes


class WHOICDError(RuntimeError):
    """Raised for real WHO ICD-11 API failures (network / non-2xx / bad JSON)."""


class WHOICDClient:
    """
    Real, credentialed WHO ICD-11 API client.

    Instantiation is cheap: no network I/O until the first real call.
    Credentials + release resolve in this priority:
        explicit constructor arg  >  environment variable  >  documented default
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        release: Optional[str] = None,
        language: str = "en",
    ) -> None:
        self.client_id = client_id or os.getenv("WHO_ICD_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("WHO_ICD_CLIENT_SECRET", "")
        self.base_url = (base_url or os.getenv("WHO_ICD_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.release = release or os.getenv("WHO_ICD_RELEASE", DEFAULT_RELEASE)
        self.language = language or "en"

        self.token_url = os.getenv("WHO_ICD_TOKEN_URL", DEFAULT_TOKEN_URL)
        self.scope = os.getenv("WHO_ICD_SCOPE", DEFAULT_SCOPE)
        try:
            self.timeout = float(os.getenv("WHO_ICD_TIMEOUT", str(DEFAULT_TIMEOUT)))
        except ValueError:
            self.timeout = DEFAULT_TIMEOUT

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _new_client(self) -> httpx.Client:
        return httpx.Client(timeout=self.timeout)

    def _mms_url(self, *parts: str) -> str:
        """Build a linearization (MMS) URL: /icd/release/11/{release}/mms[/…]."""
        tail = "/".join(quote(p, safe="") for p in parts if p)
        base = f"{self.base_url}/release/11/{self.release}/mms"
        return f"{base}/{tail}" if tail else base

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Accept-Language": self.language,
            "API-Version": "v2",
        }

    # ------------------------------------------------------------------
    # OAuth2
    # ------------------------------------------------------------------
    def _token(self, *, client: Optional[httpx.Client] = None) -> str:
        """
        Return a valid OAuth2 access token, caching it via django.core.cache
        for 55 minutes. Raises :class:`WHOICDError` when credentials are
        missing or the token endpoint returns an error — silent fallback
        would let production keep serving stale seed data forever, which is
        exactly the bug we're trying to prevent.
        """
        cached = cache.get(_TOKEN_CACHE_KEY)
        if cached:
            return cached

        if not self.client_id or not self.client_secret:
            raise WHOICDError(
                "WHO_ICD_CLIENT_ID / WHO_ICD_CLIENT_SECRET not configured "
                "(register at https://icdaccessmanagement.who.int/)"
            )

        owns_client = client is None
        http = client or self._new_client()
        try:
            logger.debug("WHO ICD-11: exchanging client_credentials at %s", self.token_url)
            resp = http.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": self.scope,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as exc:
            raise WHOICDError(f"WHO ICD-11 token endpoint unreachable: {exc}") from exc
        finally:
            if owns_client:
                http.close()

        if resp.status_code != 200:
            raise WHOICDError(
                f"WHO ICD-11 token exchange failed: HTTP {resp.status_code} — {resp.text[:200]}"
            )
        try:
            body = resp.json()
        except ValueError as exc:
            raise WHOICDError(f"WHO ICD-11 token endpoint returned non-JSON: {exc}") from exc

        token = body.get("access_token")
        if not token:
            raise WHOICDError("WHO ICD-11 token response had no access_token")

        # WHO's real expires_in is 3600s. We cap to 55m so we're never
        # serving a token that's inside the last 5 minutes of its life.
        expires_in = int(body.get("expires_in", 3600))
        ttl = min(_TOKEN_CACHE_TTL, max(60, expires_in - 60))
        cache.set(_TOKEN_CACHE_KEY, token, ttl)
        return token

    def _get_json(
        self,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        client: Optional[httpx.Client] = None,
    ) -> dict[str, Any]:
        token = self._token(client=client)
        owns_client = client is None
        http = client or self._new_client()
        try:
            resp = http.get(url, headers=self._headers(token), params=params)
        except httpx.HTTPError as exc:
            raise WHOICDError(f"WHO ICD-11 GET {url} failed: {exc}") from exc
        finally:
            if owns_client:
                http.close()

        if resp.status_code == 404:
            raise WHOICDError(f"WHO ICD-11 resource not found: {url}")
        if resp.status_code >= 400:
            raise WHOICDError(
                f"WHO ICD-11 GET {url} → HTTP {resp.status_code}: {resp.text[:200]}"
            )
        try:
            return resp.json()
        except ValueError as exc:
            raise WHOICDError(f"WHO ICD-11 returned non-JSON body for {url}: {exc}") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def search(
        self,
        q: str,
        subtree_filter: Optional[str] = None,
        use_flexisearch: bool = True,
        *,
        client: Optional[httpx.Client] = None,
    ) -> list[dict[str, Any]]:
        """
        Linearization search against ``/icd/release/11/{release}/mms/search``.

        Returns the raw ``destinationEntities`` list — each item carries at
        least ``id``, ``title``, ``theCode`` (may be empty for non-codable
        foundation matches), and ``chapter``.
        """
        if not q:
            return []
        params: dict[str, Any] = {
            "q": q,
            "useFlexisearch": "true" if use_flexisearch else "false",
            "flatResults": "true",
        }
        if subtree_filter:
            params["subtreesFilter"] = subtree_filter

        data = self._get_json(self._mms_url("search"), params=params, client=client)
        entities = data.get("destinationEntities") or []
        if not isinstance(entities, list):
            logger.warning("WHO ICD-11 search returned unexpected destinationEntities type")
            return []
        return entities

    def entity(
        self,
        entity_id: str,
        *,
        client: Optional[httpx.Client] = None,
    ) -> dict[str, Any]:
        """
        Foundation entity lookup: ``GET /icd/entity/{entity_id}``.

        Accepts either the numeric id (e.g. ``"1435254666"``) or a full
        foundation URI — for the latter, use :meth:`foundation` instead
        for a version that preserves the URI verbatim.
        """
        if not entity_id:
            raise WHOICDError("entity_id is required")
        # Strip a leading foundation URI if the caller passed the full URL.
        eid = entity_id.rsplit("/", 1)[-1] if "://" in entity_id else entity_id
        url = f"{self.base_url}/entity/{quote(eid, safe='')}"
        return self._get_json(url, client=client)

    def linearization(
        self,
        code: str,
        *,
        client: Optional[httpx.Client] = None,
    ) -> dict[str, Any]:
        """
        Linearization entity by ICD-11 MMS code:
        ``GET /icd/release/11/{release}/mms/{code}``.
        """
        if not code:
            raise WHOICDError("code is required")
        return self._get_json(self._mms_url(code), client=client)

    def foundation(
        self,
        foundation_uri: str,
        *,
        client: Optional[httpx.Client] = None,
    ) -> dict[str, Any]:
        """
        Resolve a full WHO foundation URI verbatim (e.g. an ``id`` returned
        by :meth:`search` or a ``parent``/``child`` link from another
        entity payload).
        """
        if not foundation_uri or "://" not in foundation_uri:
            raise WHOICDError(
                "foundation_uri must be a fully-qualified WHO URI "
                "(e.g. http://id.who.int/icd/entity/1435254666)"
            )
        return self._get_json(foundation_uri, client=client)

    def code_info(
        self,
        code: str,
        *,
        client: Optional[httpx.Client] = None,
    ) -> dict[str, Any]:
        """
        Code metadata: ``GET /icd/release/11/{release}/mms/codeinfo/{code}``.

        Useful for verifying that a given code is valid in the requested
        release and pulling its stem+extension breakdown.
        """
        if not code:
            raise WHOICDError("code is required")
        return self._get_json(self._mms_url("codeinfo", code), client=client)


__all__ = ["WHOICDClient", "WHOICDError"]
