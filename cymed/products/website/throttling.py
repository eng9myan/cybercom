"""
Website Public API — Rate Throttling.
Differentiated limits for read vs write (lead-gen) endpoints.
Uses DRF's cache-backed throttle with Redis (via platform CACHES["default"]).
"""

from rest_framework.throttling import AnonRateThrottle


class PublicReadThrottle(AnonRateThrottle):
    """Read endpoints: 600 requests/hour per IP (generous for CDN/crawlers)."""

    scope = "website_public_read"


class PublicWriteThrottle(AnonRateThrottle):
    """Write (lead-gen) endpoints: 20 requests/hour per IP."""

    scope = "website_public_write"


class DemoRequestThrottle(AnonRateThrottle):
    """Demo request submissions: 5/hour per IP (high-value lead, prevent spam)."""

    scope = "website_demo_request"


class ContactThrottle(AnonRateThrottle):
    """Contact message submissions: 10/hour per IP."""

    scope = "website_contact"


class PartnerApplicationThrottle(AnonRateThrottle):
    """Partner applications: 3/hour per IP (intentionally strict)."""

    scope = "website_partner_application"


class NewsletterThrottle(AnonRateThrottle):
    """Newsletter sign-ups: 5/hour per IP."""

    scope = "website_newsletter"
