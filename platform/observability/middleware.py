"""
Observability middleware — request-id propagation and access logging.

Both middleware must run outermost so downstream layers (auth, tenant, audit)
can enrich the same request id.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from django.http import HttpRequest, HttpResponse

from platform.observability.logging_config import (
    bind_request_context,
    clear_request_context,
)

logger = logging.getLogger("cybercom.observability")

REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
REQUEST_ID_RESPONSE_HEADER = "X-Request-Id"


class RequestIdMiddleware:
    """
    Accept ``X-Request-Id`` from callers or mint one via :func:`uuid.uuid4`.

    The value is attached to ``request.request_id``, echoed in the response
    header, and pushed into the log context so :class:`JsonFormatter` can
    include it in every record emitted while handling this request.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        provided = request.META.get(REQUEST_ID_HEADER, "").strip()
        # Sanity check — accept only reasonable ids to avoid header pollution.
        if provided and 0 < len(provided) <= 128 and all(
            ch.isalnum() or ch in "-_." for ch in provided
        ):
            request_id = provided
        else:
            request_id = uuid.uuid4().hex
        request.request_id = request_id

        tenant_id = str(getattr(request, "tenant_id", "") or "")
        bind_request_context(request_id=request_id, tenant_id=tenant_id)

        try:
            response = self.get_response(request)
        finally:
            clear_request_context()

        response[REQUEST_ID_RESPONSE_HEADER] = request_id
        return response


class AccessLogMiddleware:
    """
    Emit one structured access-log line per request.

    Fields: ``method, path, status, duration_ms, tenant_id, user_id,
    request_id``. Exceptions bubble up; a synthetic 500 entry is written so
    audit and log aggregation stays coherent.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        status = 500
        try:
            response = self.get_response(request)
            status = getattr(response, "status_code", 200)
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            user = getattr(request, "user", None)
            user_id = (
                getattr(user, "pk", None)
                if user is not None and getattr(user, "is_authenticated", False)
                else None
            )
            logger.info(
                "http.access",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": status,
                    "duration_ms": round(duration_ms, 2),
                    "tenant_id": str(getattr(request, "tenant_id", "") or ""),
                    "user_id": str(user_id) if user_id is not None else "",
                    "request_id": getattr(request, "request_id", ""),
                },
            )

            # Feed Prometheus counters when available — best effort.
            try:
                from platform.observability.metrics import observe_request

                observe_request(
                    method=request.method,
                    path_tpl=_path_template(request),
                    status=status,
                    tenant=str(getattr(request, "tenant_id", "") or "-"),
                    duration_seconds=duration_ms / 1000.0,
                )
            except Exception:  # pragma: no cover
                pass


def _path_template(request: HttpRequest) -> str:
    """Prefer the URL-conf route so metric cardinality stays finite."""
    try:
        match = getattr(request, "resolver_match", None)
        if match is not None and getattr(match, "route", None):
            return match.route
    except Exception:
        pass
    return request.path
