"""Per-partner rate limits.

Every authenticated call counts against the calling partner's own allowance, so one partner can never
starve another. Defaults (override with settings / environment):

    RATE_LIMIT_PARTNER   600/min   all endpoints
    RATE_LIMIT_AGENT     120/min   the ordering assistant, on top of the general limit

Counters live in Django's cache. The default cache is per process, so with several worker processes the
effective limit is per worker; configure a shared cache (for example Redis) in production for an exact limit.
Unauthenticated requests are refused by authentication before they ever reach a counter.
"""

from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class PartnerRateThrottle(SimpleRateThrottle):
    scope = "partner"

    def get_rate(self):
        return getattr(settings, "RATE_LIMIT_PARTNER", "600/min")

    def get_cache_key(self, request, view):
        partner = getattr(request, "partner", None)
        if partner is None:
            return None
        return self.cache_format % {"scope": self.scope, "ident": str(partner.id)}


class AgentRateThrottle(PartnerRateThrottle):
    scope = "agent"

    def get_rate(self):
        return getattr(settings, "RATE_LIMIT_AGENT", "120/min")
