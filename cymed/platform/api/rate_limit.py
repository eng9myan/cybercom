"""
Rate limiting service. ADR-0030 S3.3.
Production: Redis sliding window. Test: in-memory.
"""

import threading
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_at: float
    retry_after: int | None = None


class InMemoryRateLimiter:
    """
    Sliding-window in-memory rate limiter for testing and dev.
    Thread-safe via lock.
    """

    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int = 60) -> RateLimitResult:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._windows[key]
            # Evict old timestamps
            self._windows[key] = [t for t in timestamps if t > window_start]
            count = len(self._windows[key])

            if count >= limit:
                oldest = self._windows[key][0]
                reset_at = oldest + window_seconds
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=int(reset_at - now) + 1,
                )
            self._windows[key].append(now)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit - count - 1,
                reset_at=now + window_seconds,
            )

    def reset(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)

    def reset_all(self) -> None:
        with self._lock:
            self._windows.clear()


class RateLimitService:
    """
    Main rate limit service. Resolves limit config from ApiRateLimit model
    and delegates to backend (in-memory or Redis).
    """

    def __init__(self, backend=None):
        self._backend = backend or InMemoryRateLimiter()

    def check_tenant(self, tenant_id: str, requests_per_minute: int = 60) -> RateLimitResult:
        key = f"rl:tenant:{tenant_id}:minute"
        return self._backend.check(key, requests_per_minute, 60)

    def check_user(self, user_id: str, requests_per_minute: int = 30) -> RateLimitResult:
        key = f"rl:user:{user_id}:minute"
        return self._backend.check(key, requests_per_minute, 60)

    def check_application(self, app_id: str, requests_per_minute: int = 120) -> RateLimitResult:
        key = f"rl:app:{app_id}:minute"
        return self._backend.check(key, requests_per_minute, 60)

    def check_ip(self, ip: str, requests_per_minute: int = 20) -> RateLimitResult:
        key = f"rl:ip:{ip}:minute"
        return self._backend.check(key, requests_per_minute, 60)

    def check_burst(self, key_prefix: str, burst_size: int = 20) -> RateLimitResult:
        key = f"rl:burst:{key_prefix}:second"
        return self._backend.check(key, burst_size, 1)

    def get_limit_from_model(self, tenant_id=None, application_id=None):
        """Load rate limit config from DB, fall back to defaults."""
        try:
            from django.db.models import Q

            from .models import ApiRateLimit

            rl = (
                ApiRateLimit.objects.filter(
                    is_active=True,
                )
                .filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))
                .order_by("-tenant_id")
                .first()
            )
            if rl:
                return rl.requests_per_minute, rl.burst_size
        except Exception:
            pass
        return 60, 20

    def reset(self, key: str) -> None:
        self._backend.reset(key)

    def reset_all(self) -> None:
        self._backend.reset_all()


# Module-level singleton (replaced in tests)
_rate_limiter = RateLimitService()


def get_rate_limiter() -> RateLimitService:
    return _rate_limiter
