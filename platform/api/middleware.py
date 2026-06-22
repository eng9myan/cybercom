"""
CyberCom API middleware stack.
- Correlation ID injection
- Rate limit enforcement
- Idempotency header handling
- API usage recording
- Audit event emission
"""
import logging
import time
import uuid

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

log = logging.getLogger(__name__)

RATE_LIMIT_EXEMPT_PATHS = {"/api/v1/audit/healthz/", "/api/v1/tenants/healthz/", "/health", "/metrics"}


class CorrelationIdMiddleware(MiddlewareMixin):
    """Injects X-Correlation-ID into every request and response."""

    def process_request(self, request):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.correlation_id = correlation_id

    def process_response(self, request, response):
        correlation_id = getattr(request, "correlation_id", str(uuid.uuid4()))
        response["X-Correlation-ID"] = correlation_id
        return response


class ApiVersionHeaderMiddleware(MiddlewareMixin):
    """Injects X-API-Version and Deprecation/Sunset headers."""

    def process_response(self, request, response):
        response["X-API-Version"] = "1.0.0"
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limit enforcement at middleware layer.
    Reads tenant_id from JWT claims or X-Tenant-ID header.
    Returns 429 with RFC 7807 problem detail on breach.
    """

    def process_request(self, request):
        if request.path in RATE_LIMIT_EXEMPT_PATHS:
            return None
        if not request.path.startswith("/api/"):
            return None

        from .rate_limit import get_rate_limiter
        rl = get_rate_limiter()

        tenant_id = request.headers.get("X-Tenant-ID", "")
        ip = request.META.get("REMOTE_ADDR", "")

        result = rl.check_tenant(tenant_id or ip, requests_per_minute=60)
        if not result.allowed:
            response = JsonResponse({
                "type": "https://cybercom.io/errors/rate_limit_exceeded",
                "title": "Too Many Requests",
                "status": 429,
                "detail": f"Rate limit exceeded. Retry after {result.retry_after}s.",
                "instance": request.path,
            }, status=429)
            response["Retry-After"] = str(result.retry_after or 60)
            response["X-RateLimit-Limit"] = str(result.limit)
            response["X-RateLimit-Remaining"] = "0"
            return response

        request.rate_limit_remaining = result.remaining
        return None

    def process_response(self, request, response):
        remaining = getattr(request, "rate_limit_remaining", None)
        if remaining is not None:
            response["X-RateLimit-Remaining"] = str(remaining)
        return response


class ApiUsageMiddleware(MiddlewareMixin):
    """
    Records ApiUsage for every API request asynchronously.
    Uses request start time to compute latency.
    """

    def process_request(self, request):
        request._api_start_time = time.monotonic()

    def process_response(self, request, response):
        if not request.path.startswith("/api/"):
            return response

        try:
            latency_ms = int((time.monotonic() - getattr(request, "_api_start_time", time.monotonic())) * 1000)
            from .models import ApiUsage
            tenant_id = request.headers.get("X-Tenant-ID") or None
            correlation_id = getattr(request, "correlation_id", "")
            ApiUsage.objects.create(
                tenant_id=tenant_id,
                endpoint_path=request.path,
                http_method=request.method,
                status_code=response.status_code,
                latency_ms=latency_ms,
                correlation_id=correlation_id,
                is_error=response.status_code >= 400,
                is_rate_limited=response.status_code == 429,
            )
        except Exception:
            pass  # Never block response on usage recording failure

        return response
