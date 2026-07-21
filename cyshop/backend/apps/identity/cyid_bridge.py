"""
CyID ecosystem, Phase 3 — bridges a real CyID (Keycloak RS256) token into
a cyshop-local session. cyshop's own JWTAuthentication (HS256, unchanged)
stays the auth path for every existing endpoint; this is the one new
entry point that accepts a CyID token and mints an equivalent cyshop
session, so a person who enrolled once in CyID (platform.cyidentity,
software-token MVP — see platform/cyidentity/services.py::CyIDService)
can reach cyshop with the same credential instead of a separate signup.

cyshop and CyIdentity are separate services/databases — this verifies the
token against the real shared JWKS endpoint (no cross-process trust
shortcut), same as shared/auth/auth_middleware.py does for cymed/cycom,
just implemented standalone since cyshop doesn't import that shared
middleware module.
"""

import datetime
import logging

import jwt
from django.conf import settings
from jwt import PyJWKClient

logger = logging.getLogger("cyshop.cyid_bridge")

_jwks_client: "PyJWKClient | None" = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.CYIDENTITY_JWKS_URI, cache_keys=True)
    return _jwks_client


class CyIDTokenError(Exception):
    pass


def verify_cyid_token(token: str) -> dict:
    """Real RS256/JWKS verification against the shared CyIdentity realm —
    raises CyIDTokenError on any invalid/expired/unparseable token, never
    trusts an unverified `person_id` claim from the caller."""
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"require": ["exp", "iat", "sub"], "verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise CyIDTokenError("CyID token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise CyIDTokenError(f"Invalid CyID token: {exc}") from exc


def exchange_cyid_token(token: str, tenant_id: str) -> dict:
    """
    Verifies the CyID token, then finds-or-JIT-provisions a cyshop User
    for this (person, tenant) pair and mints a real cyshop session —
    exact same token shape/fields UserLoginSerializer.validate() returns,
    so every existing cyshop client (mobile app, frontend) handles this
    response identically to a normal login.
    """
    from apps.identity.models import RoleAssignment, User, UserSession
    from apps.tenants.models import Tenant

    claims = verify_cyid_token(token)
    person_id = claims.get("person_id")
    if not person_id:
        raise CyIDTokenError("CyID token has no person_id claim — not a CyID-issued token.")
    email = claims.get("email", "")

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist as exc:
        raise CyIDTokenError(f"Unknown tenant: {tenant_id}") from exc

    user = User.objects.filter(cyid_person_id=person_id, tenant_id=tenant.id).first()
    if user is None:
        # First time this CyID person has reached this cyshop tenant —
        # JIT-provision, same "link a new tenant on first visit" pattern
        # as CyIDService.link_tenant_profile on the Keycloak-backed side.
        base_username = (email.split("@")[0] if email else f"cyid-{person_id}")
        username = base_username
        suffix = 0
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username}-{suffix}"
        user = User.objects.create(
            username=username,
            email=email,
            tenant_id=tenant.id,
            cyid_person_id=person_id,
        )
        user.set_unusable_password()  # real auth happens via CyID, not a local password
        user.save(update_fields=["password"])
        logger.info("JIT-provisioned cyshop user %s for CyID person %s in tenant %s", username, person_id, tenant.id)

    assignments = RoleAssignment.objects.filter(user=user)
    scopes = [a.role.code for a in assignments]

    access_payload = {
        "user_id": str(user.id),
        "username": user.username,
        "tenant_id": str(tenant.id),
        "scopes": scopes,
        "type": "access",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
    }
    refresh_payload = {
        "user_id": str(user.id),
        "type": "refresh",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")

    from django.utils import timezone

    UserSession.objects.create(
        user=user,
        tenant_id=tenant.id,
        token=access_token,
        expires_at=timezone.now() + datetime.timedelta(hours=2),
    )

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "scopes": scopes,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
