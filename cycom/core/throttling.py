from rest_framework.throttling import ScopedRateThrottle


class PublicWriteRateThrottle(ScopedRateThrottle):
    """Rate-limits only mutating requests under the `website_public_write`
    scope (settings.py's `DEFAULT_THROTTLE_RATES`, defined but never wired
    to a view until now). Safe method requests (GET/HEAD/OPTIONS) pass
    through untouched — several public views combine polling reads with a
    write on the same URL (e.g. livechat's message poll+send, elearning's
    lesson-progress check+complete), and a chat widget polling every few
    seconds would blow through a 30/hour write budget in under a minute if
    plain ScopedRateThrottle applied to the whole view."""

    scope = "website_public_write"

    def allow_request(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return super().allow_request(request, view)
