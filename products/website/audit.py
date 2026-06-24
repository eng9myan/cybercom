"""
Website API audit logging utility.
Writes to both WebsiteApiLog (lightweight analytics) and platform AuditLog (compliance).
"""
import time
import uuid
from typing import Optional

from django.utils import timezone


def log_website_request(
    request,
    endpoint: str,
    status_code: int,
    resource_type: str = "",
    resource_id: str = "",
    was_throttled: bool = False,
    error_detail: str = "",
    start_time: Optional[float] = None,
) -> None:
    """
    Write a WebsiteApiLog entry. Non-blocking: import is deferred to avoid
    circular imports at module load time. Failures are swallowed to prevent
    public API errors from masking the original response.
    """
    try:
        from .models import WebsiteApiLog

        response_time_ms = 0
        if start_time is not None:
            response_time_ms = int((time.monotonic() - start_time) * 1000)

        ip = _get_client_ip(request)

        WebsiteApiLog.objects.create(
            endpoint=endpoint,
            method=request.method,
            status_code=status_code,
            ip_address=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            referrer=request.META.get("HTTP_REFERER", "")[:200],
            response_time_ms=response_time_ms,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else "",
            was_throttled=was_throttled,
            error_detail=error_detail[:500],
        )
    except Exception:
        pass


def log_lead_event(
    request,
    action: str,
    resource_type: str,
    resource_id: str,
    status: str = "success",
    details: Optional[dict] = None,
) -> None:
    """
    Write a platform AuditLog entry for lead-gen events (demo requests, contacts, partner apps).
    These are PUBLIC category events with DATA_CLASSIFICATION=PUBLIC.
    """
    try:
        from platform.audit.models import AuditLog, AuditAction, AuditStatus

        ip = _get_client_ip(request)

        AuditLog.objects.create(
            tenant_id=None,
            user_id="public",
            session_id="",
            trace_id=str(uuid.uuid4()),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            status=AuditStatus.SUCCESS if status == "success" else AuditStatus.FAILURE,
            ip_address=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            request_path=request.path,
            request_method=request.method,
            description=f"Website public API: {action} on {resource_type}",
            details=details or {},
        )
    except Exception:
        pass


def _get_client_ip(request) -> Optional[str]:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
