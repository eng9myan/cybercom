"""
Idempotency key service. ADR-0030 S3.1: safe retries without double processing.
Header: Idempotency-Key (max 255 chars).
Retention: 24 hours by default.
"""

import hashlib
from datetime import timedelta

from django.utils import timezone

from .models import IdempotencyKey


class IdempotencyService:
    """
    Checks and stores idempotency keys.

    Usage:
        svc = IdempotencyService()
        result = svc.check_or_store(key, tenant_id, method, path, body)
        if result.is_replay:
            return result.cached_response()
        # process request...
        svc.complete(result.record, status_code, response_body)
    """

    RETENTION_HOURS = 24

    def _body_hash(self, body: str) -> str:
        return hashlib.sha256(body.encode()).hexdigest()

    def get(self, key: str, tenant_id=None) -> IdempotencyKey | None:
        try:
            return IdempotencyKey.objects.get(key=key, tenant_id=tenant_id)
        except IdempotencyKey.DoesNotExist:
            return None

    def store(
        self,
        key: str,
        tenant_id=None,
        application_id=None,
        method: str = "POST",
        path: str = "",
        body: str = "",
    ) -> IdempotencyKey:
        return IdempotencyKey.objects.create(
            key=key,
            tenant_id=tenant_id,
            application_id=application_id,
            request_method=method,
            request_path=path,
            request_hash=self._body_hash(body),
            expires_at=timezone.now() + timedelta(hours=self.RETENTION_HOURS),
        )

    def check_or_store(
        self,
        key: str,
        tenant_id=None,
        application_id=None,
        method: str = "POST",
        path: str = "",
        body: str = "",
    ) -> "IdempotencyCheckResult":
        existing = self.get(key, tenant_id)
        if existing:
            if existing.is_expired:
                existing.delete()
            elif not existing.processing:
                return IdempotencyCheckResult(is_replay=True, record=existing)
            else:
                return IdempotencyCheckResult(is_replay=False, record=existing, in_flight=True)

        record = self.store(key, tenant_id, application_id, method, path, body)
        return IdempotencyCheckResult(is_replay=False, record=record)

    def complete(self, record: IdempotencyKey, status_code: int, response_body: str) -> None:
        record.complete(status_code, response_body)

    def purge_expired(self) -> int:
        deleted, _ = IdempotencyKey.objects.filter(expires_at__lt=timezone.now()).delete()
        return deleted


class IdempotencyCheckResult:
    def __init__(self, is_replay: bool, record: IdempotencyKey, in_flight: bool = False):
        self.is_replay = is_replay
        self.record = record
        self.in_flight = in_flight

    def cached_response(self) -> tuple[int, str]:
        return self.record.response_status, self.record.response_body
