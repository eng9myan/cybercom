"""
Website Public API — Rate Throttling.
Differentiated limits for read vs write (lead-gen) endpoints.
Uses DRF's cache-backed throttle with Redis (via platform CACHES["default"]).
"""
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class PublicReadThrottle(AnonRateThrottle):
    """Read endpoints: 600 requests/hour per IP (generous for CDN/crawlers)."""
    scope = "website_public_read"
    rate = "600/hour"


class PublicWriteThrottle(AnonRateThrottle):
    """Write (lead-gen) endpoints: 20 requests/hour per IP."""
    scope = "website_public_write"
    rate = "20/hour"


class DemoRequestThrottle(AnonRateThrottle):
    """Demo request submissions: 5/hour per IP (high-value lead, prevent spam)."""
    scope = "website_demo_request"
    rate = "5/hour"


class ContactThrottle(AnonRateThrottle):
    """Contact message submissions: 10/hour per IP."""
    scope = "website_contact"
    rate = "10/hour"


class PartnerApplicationThrottle(AnonRateThrottle):
    """Partner applications: 3/hour per IP (intentionally strict)."""
    scope = "website_partner_application"
    rate = "3/hour"


class NewsletterThrottle(AnonRateThrottle):
    """Newsletter sign-ups: 5/hour per IP."""
    scope = "website_newsletter"
    rate = "5/hour"
