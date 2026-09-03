"""
Security middleware — headers, client integrity attestation, and rate limiting.

Order recommendation (outer -> inner):
    SecurityHeadersMiddleware        # writes response headers
    ClientIntegrityMiddleware        # tags requests, optional block
    RateLimitMiddleware              # per-IP token bucket via cache

All middleware are safe when the cache backend is unavailable (they degrade
open rather than hard-fail) but log a warning.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse

logger = logging.getLogger("cybercom.security")


# ---------------------------------------------------------------------------
# Default header set — override via settings.PLATFORM_SECURITY_HEADERS
# ---------------------------------------------------------------------------
_DEFAULT_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
    "Permissions-Policy": "geolocation=(), camera=(self)",
}


class SecurityHeadersMiddleware:
    """Set hardening headers on every response.

    Threat model coverage:
      * HSTS       — protocol-downgrade / SSL-strip
      * nosniff    — MIME-sniffing XSS
      * DENY       — clickjacking
      * Referrer   — cross-origin URL leaks
      * CSP        — default-deny inline / third-party sources
      * Permissions-Policy — disables geolocation, restricts camera to same-origin
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        overrides = getattr(settings, "PLATFORM_SECURITY_HEADERS", {}) or {}
        self.headers = {**_DEFAULT_HEADERS, **overrides}

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        for header, value in self.headers.items():
            # Don't clobber an intentional per-view override.
            if header not in response:
                response[header] = value
        return response


class ClientIntegrityMiddleware:
    """
    Consume an ``X-Client-Integrity`` attestation header from mobile clients.

    The header is produced by device-side attestation libraries such as Google
    Play Integrity API or Apple App Attest and passed opaquely. This middleware
    stores it on ``request.client_integrity`` for downstream views and logs
    presence/absence per request.

    It does NOT block by default. Set ``PLATFORM_ENFORCE_INTEGRITY = True`` to
    reject requests missing the header (returns 403). Server-to-server clients
    that predate attestation should be routed via allowlisted paths — see
    ``PLATFORM_INTEGRITY_EXEMPT_PATHS``.
    """

    HEADER = "HTTP_X_CLIENT_INTEGRITY"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.enforce = bool(getattr(settings, "PLATFORM_ENFORCE_INTEGRITY", False))
        self.exempt_paths = tuple(
            getattr(settings, "PLATFORM_INTEGRITY_EXEMPT_PATHS", (
                "/health",
                "/metrics",
                "/admin/",
                "/api/schema/",
                "/api/docs/",
                "/api/redoc/",
            ))
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        token = request.META.get(self.HEADER, "")
        request.client_integrity = token or None
        request.client_integrity_verified = False  # verification is opaque here

        path = request.path
        exempt = any(path.startswith(prefix) for prefix in self.exempt_paths)

        if not token and self.enforce and not exempt:
            logger.warning(
                "client_integrity.missing",
                extra={"path": path, "remote": request.META.get("REMOTE_ADDR")},
            )
            return JsonResponse(
                {"error": "client_integrity_required"}, status=403
            )

        if token:
            logger.debug(
                "client_integrity.present",
                extra={"path": path, "token_len": len(token)},
            )

        return self.get_response(request)


class RateLimitMiddleware:
    """
    Per-IP token bucket implemented on ``django.core.cache``.

    Two buckets:
      * Default : ``PLATFORM_RATE_LIMIT_PER_MIN`` (default 60) req / minute
      * Admin   : ``PLATFORM_RATE_LIMIT_ADMIN_PER_MIN`` (default 500) req / min
                  applied to paths starting with ``/admin/``

    Uses a fixed 60-second window with atomic ``cache.incr``. When the cache
    backend errors, requests are allowed through and a warning is logged —
    availability over strict throttling.
    """

    WINDOW_SECONDS = 60

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response
        self.limit_default = int(getattr(settings, "PLATFORM_RATE_LIMIT_PER_MIN", 60))
        self.limit_admin = int(getattr(settings, "PLATFORM_RATE_LIMIT_ADMIN_PER_MIN", 500))
        self.enabled = bool(getattr(settings, "PLATFORM_RATE_LIMIT_ENABLED", True))
        self.exempt_paths = tuple(
            getattr(settings, "PLATFORM_RATE_LIMIT_EXEMPT_PATHS", (
                "/health",
                "/health/liveness",
                "/health/readiness",
                "/metrics",
            ))
        )

    def _client_ip(self, request: HttpRequest) -> str:
        fwd = request.META.get("HTTP_X_FORWARDED_FOR")
        if fwd:
            return fwd.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self.enabled:
            return self.get_response(request)

        path = request.path
        if any(path.startswith(p) for p in self.exempt_paths):
            return self.get_response(request)

        limit = self.limit_admin if path.startswith("/admin/") else self.limit_default
        ip = self._client_ip(request)
        window = int(time.time() // self.WINDOW_SECONDS)
        key = f"ratelimit:{ip}:{window}"

        try:
            # cache.add is atomic-ish; incr requires an existing key.
            cache.add(key, 0, timeout=self.WINDOW_SECONDS * 2)
            current = cache.incr(key)
        except Exception as exc:  # pragma: no cover — cache outage
            logger.warning("ratelimit.cache_error: %s", exc)
            return self.get_response(request)

        if current > limit:
            logger.warning(
                "ratelimit.exceeded",
                extra={"ip": ip, "path": path, "count": current, "limit": limit},
            )
            retry_after = self.WINDOW_SECONDS - int(time.time() % self.WINDOW_SECONDS)
            response = JsonResponse(
                {"error": "rate_limit_exceeded", "retry_after": retry_after},
                status=429,
            )
            response["Retry-After"] = str(retry_after)
            return response

        return self.get_response(request)
