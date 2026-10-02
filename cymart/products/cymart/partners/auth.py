"""API-key authentication — the only auth this product has. There is no
customer-login concept here; a licensed partner authenticates with its
own key, scoped to itself, on every call."""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Partner


class PartnerUser:
    """A minimal DRF-compatible stand-in for request.user."""

    is_authenticated = True

    def __init__(self, partner: Partner):
        self.partner = partner
        self.id = partner.id

    def __str__(self):
        return str(self.partner.name)


class PartnerAPIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw_key = request.headers.get("X-API-Key")
        if not raw_key:
            return None
        try:
            partner = Partner.objects.get(api_key_hash=Partner.hash_key(raw_key), is_active=True)
        except Partner.DoesNotExist:
            raise AuthenticationFailed("Invalid API key.")
        request.partner = partner
        return (PartnerUser(partner), None)
