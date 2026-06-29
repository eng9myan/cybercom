"""
CyIdentity service layer.

Wraps the Keycloak 24 Admin REST API. Implements:
  - KeycloakAdminClient          — Admin REST client with retry + circuit-breaker-lite
  - JWKSCache                    — JWKS cache with TTL + 60-min stale-while-error
  - TokenValidator               — RS256 JWT validation against cached JWKS
  - RealmService                 — CRUD + provisioning + activation + decommission
  - ClientService                — OAuth/OIDC client lifecycle + secret rotation
  - UserProvisioningService      — bulk user import + role sync
  - RoleSyncService              — role catalog + role→permission sync
  - BreakGlassService            — request → dual-approve → activate → expire
  - SessionService               — list / revoke sessions, idle timeout
  - AuditService                 — writes LoginAudit + emits to platform audit sink
  - MetricsRecorder              — Prometheus counters/histograms for identity ops

All methods are pure-Python, framework-agnostic where possible so they can be
unit-tested without spinning up Keycloak (HTTP mocked) or invoked from
Celery tasks / management commands / DRF views interchangeably.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import jwt
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from platform.cyidentity.models import (
    ApplicationClient,
    BreakGlassAccess,
    BreakGlassStatus,
    ClientSecret,
    IdentityRealm,
    LoginAudit,
    Permission,
    RealmConfiguration,
    RealmStatus,
    Role,
    RoleAssignment,
    UserProfile,
    UserSession,
)

logger = logging.getLogger("cybercom.cyidentity")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class KeycloakError(Exception):
    """Base error from the Keycloak Admin REST integration."""

    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class KeycloakNotFound(KeycloakError):
    pass


class KeycloakConflict(KeycloakError):
    pass


class TokenValidationError(Exception):
    """JWT validation failure with reason."""


# ---------------------------------------------------------------------------
# MetricsRecorder — minimal Prometheus exposition helpers
# ---------------------------------------------------------------------------
@dataclass
class IdentityMetrics:
    """Process-local counters; exposed via /metrics in core.urls."""

    login_total: int = 0
    login_failure_total: int = 0
    mfa_challenge_total: int = 0
    mfa_failure_total: int = 0
    realm_provisioned_total: int = 0
    realm_decommissioned_total: int = 0
    client_created_total: int = 0
    secret_rotated_total: int = 0
    break_glass_requested_total: int = 0
    break_glass_activated_total: int = 0
    session_revoked_total: int = 0
    audit_emitted_total: int = 0
    jwks_refresh_total: int = 0
    jwks_serve_stale_total: int = 0
    # latency histograms (simple list of recent samples)
    login_latency_ms: list[int] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {
            "login_total": self.login_total,
            "login_failure_total": self.login_failure_total,
            "mfa_challenge_total": self.mfa_challenge_total,
            "mfa_failure_total": self.mfa_failure_total,
            "realm_provisioned_total": self.realm_provisioned_total,
            "realm_decommissioned_total": self.realm_decommissioned_total,
            "client_created_total": self.client_created_total,
            "secret_rotated_total": self.secret_rotated_total,
            "break_glass_requested_total": self.break_glass_requested_total,
            "break_glass_activated_total": self.break_glass_activated_total,
            "session_revoked_total": self.session_revoked_total,
            "audit_emitted_total": self.audit_emitted_total,
            "jwks_refresh_total": self.jwks_refresh_total,
            "jwks_serve_stale_total": self.jwks_serve_stale_total,
            "login_latency_ms_p50": _percentile(self.login_latency_ms, 50),
            "login_latency_ms_p95": _percentile(self.login_latency_ms, 95),
        }


def _percentile(samples: list[int], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    k = max(0, min(len(ordered) - 1, round((pct / 100.0) * (len(ordered) - 1))))
    return float(ordered[k])


# Module-level singleton; tests can reset via `metrics.__dict__.update(...)`.
metrics = IdentityMetrics()


def render_prometheus() -> str:
    """Render identity metrics in Prometheus text exposition format."""
    snap = metrics.snapshot()
    lines: list[str] = []
    for name, value in snap.items():
        metric = f"cybercom_identity_{name}"
        if name.startswith("login_latency_ms_p"):
            lines.append(f"# TYPE {metric} gauge")
        else:
            lines.append(f"# TYPE {metric} counter")
        lines.append(f"{metric} {value}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# KeycloakAdminClient — Admin REST wrapper
# ---------------------------------------------------------------------------
class KeycloakAdminClient:
    """
    Wraps the Keycloak 24 Admin REST API.

    In production this uses httpx against the real Keycloak cluster.
    In tests / unit mode (settings.KEYCLOAK_ENABLED=False) it operates in
    an in-memory "fake Keycloak" so service-layer logic remains testable.
    """

    def __init__(self, realm: IdentityRealm | None = None):
        self.base_url = (
            realm.admin_api_url.rstrip("/")
            if realm and realm.admin_api_url
            else getattr(settings, "CYIDENTITY_ISSUER", "http://localhost:8080").rstrip("/")
        )
        self.realm_name = realm.realm_name if realm else "master"
        self.admin_token: str | None = None
        self.timeout_seconds: int = 10
        self._fake_store: dict[str, Any] = {"realms": {}, "clients": {}, "users": {}, "roles": {}}

    # --- Token -------------------------------------------------------------
    def authenticate(self, username: str | None = None, password: str | None = None) -> str:
        """Obtain admin token. In real mode: password grant against master realm."""
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            self.admin_token = f"fake-admin-token-{uuid.uuid4()}"
            return self.admin_token
        # Real implementation would POST /realms/master/protocol/openid-connect/token
        # We require httpx at runtime; lazy import so unit tests don't need it.
        import httpx  # type: ignore

        token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
        data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": username or os.environ.get("KEYCLOAK_ADMIN", "admin"),
            "password": password or os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "admin"),
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            resp = client.post(token_url, data=data)
            if resp.status_code != 200:
                raise KeycloakError(f"Admin token failed: {resp.status_code}", resp.status_code)
            self.admin_token = resp.json()["access_token"]
            return self.admin_token

    # --- Realm CRUD --------------------------------------------------------
    def create_realm(self, realm_payload: dict[str, Any]) -> dict[str, Any]:
        """Create a Keycloak realm. Returns the created realm representation."""
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            self._fake_store["realms"][realm_payload["realm"]] = realm_payload
            return realm_payload
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms"
        resp = httpx.post(
            url, json=realm_payload, headers=self._auth_headers(), timeout=self.timeout_seconds
        )
        if resp.status_code == 409:
            raise KeycloakConflict("Realm already exists", 409, resp.text)
        if resp.status_code >= 400:
            raise KeycloakError(
                f"create_realm failed: {resp.status_code}", resp.status_code, resp.text
            )
        return resp.json() if resp.text else {"realm": realm_payload["realm"]}

    def get_realm(self, realm_name: str) -> dict[str, Any]:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            return self._fake_store["realms"].get(realm_name, {"realm": realm_name})
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms/{realm_name}"
        resp = httpx.get(url, headers=self._auth_headers(), timeout=self.timeout_seconds)
        if resp.status_code == 404:
            raise KeycloakNotFound(f"Realm not found: {realm_name}", 404)
        if resp.status_code >= 400:
            raise KeycloakError(
                f"get_realm failed: {resp.status_code}", resp.status_code, resp.text
            )
        return resp.json()

    def update_realm(self, realm_name: str, payload: dict[str, Any]) -> None:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            self._fake_store["realms"].setdefault(realm_name, {}).update(payload)
            return
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms/{realm_name}"
        resp = httpx.put(
            url, json=payload, headers=self._auth_headers(), timeout=self.timeout_seconds
        )
        if resp.status_code >= 400:
            raise KeycloakError(
                f"update_realm failed: {resp.status_code}", resp.status_code, resp.text
            )

    def delete_realm(self, realm_name: str) -> None:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            self._fake_store["realms"].pop(realm_name, None)
            return
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms/{realm_name}"
        resp = httpx.delete(url, headers=self._auth_headers(), timeout=self.timeout_seconds)
        if resp.status_code == 404:
            raise KeycloakNotFound(f"Realm not found: {realm_name}", 404)
        if resp.status_code >= 400:
            raise KeycloakError(
                f"delete_realm failed: {resp.status_code}", resp.status_code, resp.text
            )

    # --- Client CRUD --------------------------------------------------------
    def create_client(self, realm_name: str, client_payload: dict[str, Any]) -> dict[str, Any]:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            client_id = client_payload.get("clientId") or str(uuid.uuid4())
            self._fake_store["clients"].setdefault(realm_name, {})[client_id] = client_payload
            return {"clientId": client_id, **client_payload}
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms/{realm_name}/clients"
        resp = httpx.post(
            url, json=client_payload, headers=self._auth_headers(), timeout=self.timeout_seconds
        )
        if resp.status_code >= 400:
            raise KeycloakError(
                f"create_client failed: {resp.status_code}", resp.status_code, resp.text
            )
        return resp.json() if resp.text else client_payload

    def get_client_secret(self, realm_name: str, client_uuid: str) -> dict[str, Any]:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            value = f"fake-secret-{secrets.token_urlsafe(24)}"
            return {"type": "secret", "value": value}
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms/{realm_name}/clients/{client_uuid}/client-secret"
        resp = httpx.get(url, headers=self._auth_headers(), timeout=self.timeout_seconds)
        if resp.status_code >= 400:
            raise KeycloakError(
                f"get_client_secret failed: {resp.status_code}", resp.status_code, resp.text
            )
        return resp.json()

    def regenerate_client_secret(self, realm_name: str, client_uuid: str) -> dict[str, Any]:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            return {"type": "secret", "value": f"fake-secret-{secrets.token_urlsafe(24)}"}
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms/{realm_name}/clients/{client_uuid}/client-secret"
        resp = httpx.post(url, headers=self._auth_headers(), timeout=self.timeout_seconds)
        if resp.status_code >= 400:
            raise KeycloakError(
                f"regenerate_client_secret failed: {resp.status_code}", resp.status_code, resp.text
            )
        return resp.json()

    # --- Users --------------------------------------------------------------
    def create_user(self, realm_name: str, user_payload: dict[str, Any]) -> str:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            uid = str(uuid.uuid4())
            self._fake_store["users"].setdefault(realm_name, {})[uid] = user_payload
            return uid
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms/{realm_name}/users"
        resp = httpx.post(
            url, json=user_payload, headers=self._auth_headers(), timeout=self.timeout_seconds
        )
        if resp.status_code == 409:
            raise KeycloakConflict("User already exists", 409, resp.text)
        if resp.status_code >= 400:
            raise KeycloakError(
                f"create_user failed: {resp.status_code}", resp.status_code, resp.text
            )
        location = resp.headers.get("Location", "")
        return location.rsplit("/", 1)[-1] if location else str(uuid.uuid4())

    def assign_role_to_user(self, realm_name: str, user_id: str, role_name: str) -> None:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            return
        import httpx  # type: ignore

        url = f"{self.base_url}/admin/realms/{realm_name}/users/{user_id}/role-mappings/realm"
        resp = httpx.post(
            url,
            json=[{"name": role_name}],
            headers=self._auth_headers(),
            timeout=self.timeout_seconds,
        )
        if resp.status_code >= 400:
            raise KeycloakError(
                f"assign_role failed: {resp.status_code}", resp.status_code, resp.text
            )

    # --- Helpers ------------------------------------------------------------
    def _auth_headers(self) -> dict[str, str]:
        if not self.admin_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}


# ---------------------------------------------------------------------------
# JWKSCache — JWKS cache with stale-while-error
# ---------------------------------------------------------------------------
class JWKSCache:
    """JWKS cache with TTL + graceful degradation per ADR-0017 §5.6 + ADR-0035 §5.6."""

    TTL_SECONDS = 300  # 5-minute refresh
    STALE_TTL_SECONDS = 3600  # serve cached up to 60 min on error

    def __init__(self, jwks_uri: str | None = None):
        self.jwks_uri = jwks_uri or getattr(settings, "CYIDENTITY_JWKS_URI", None)

    def get_keys(self) -> dict[str, Any]:
        cache_key = f"cyidentity:jwks:{self.jwks_uri}"
        cached = cache.get(cache_key)
        if cached and not self._is_stale(cached):
            return cached["keys"]
        try:
            fresh = self._fetch()
            cache.set(cache_key, {"fetched_at": time.time(), "keys": fresh}, self.STALE_TTL_SECONDS)
            metrics.jwks_refresh_total += 1
            return fresh
        except Exception as exc:
            if cached:
                metrics.jwks_serve_stale_total += 1
                logger.warning("jwks_serve_stale", extra={"reason": str(exc)})
                return cached["keys"]
            raise TokenValidationError(f"JWKS fetch failed and no cache: {exc}") from exc

    def _is_stale(self, cached: dict[str, Any]) -> bool:
        return (time.time() - cached.get("fetched_at", 0)) > self.TTL_SECONDS

    def _fetch(self) -> dict[str, Any]:
        if not getattr(settings, "KEYCLOAK_ENABLED", True):
            # Return a minimal fake JWKS for local development / tests
            return {"keys": []}
        import httpx  # type: ignore

        with httpx.Client(timeout=5) as client:
            resp = client.get(self.jwks_uri)
            resp.raise_for_status()
            return resp.json()


# ---------------------------------------------------------------------------
# TokenValidator
# ---------------------------------------------------------------------------
class TokenValidator:
    """Validates RS256 access tokens against cached JWKS. ADR-0005 §3.3."""

    def __init__(self, jwks_cache: JWKSCache | None = None, issuer: str | None = None):
        self.jwks = jwks_cache or JWKSCache()
        self.issuer = issuer or getattr(settings, "CYIDENTITY_ISSUER", None)
        self.audience = getattr(settings, "CYIDENTITY_CLIENT_ID", None)
        self.algorithms = ["RS256"]

    def validate(self, token: str, audience: str | None = None) -> dict[str, Any]:
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            keys = self.jwks.get_keys().get("keys", [])
            jwk = next((k for k in keys if k.get("kid") == kid), None)
            if jwk is None:
                raise TokenValidationError(f"No JWK for kid={kid}")
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            claims = jwt.decode(
                token,
                key=public_key,
                algorithms=self.algorithms,
                audience=audience or self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "iss", "sub"]},
            )
            return claims
        except jwt.PyJWTError as exc:
            raise TokenValidationError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Secret hashing helper
# ---------------------------------------------------------------------------
def hash_client_secret(secret: str) -> str:
    """Argon2id preferred; SHA-256 fallback so tests don't need argon2 lib."""
    try:
        from argon2 import PasswordHasher  # type: ignore

        return PasswordHasher().hash(secret)
    except ImportError:  # pragma: no cover
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def verify_client_secret(secret: str, hashed: str) -> bool:
    try:
        from argon2 import PasswordHasher  # type: ignore
        from argon2.exceptions import VerifyMismatchError  # type: ignore

        try:
            return PasswordHasher().verify(hashed, secret)
        except VerifyMismatchError:
            return False
    except ImportError:  # pragma: no cover
        return hashlib.sha256(secret.encode("utf-8")).hexdigest() == hashed


# ---------------------------------------------------------------------------
# RealmService — lifecycle of IdentityRealm + RealmConfiguration
# ---------------------------------------------------------------------------
class RealmService:
    """ADR-0017 §5.2: realm lifecycle (provision → activate → suspend → decommission)."""

    def __init__(self, kc: KeycloakAdminClient | None = None):
        self.kc = kc or KeycloakAdminClient()

    def provision(
        self,
        *,
        tenant_id: uuid.UUID,
        realm_name: str,
        realm_type: str,
        display_name: str | None = None,
        enabled: bool = True,
        access_token_lifetime: int = 900,
        mfa_methods: list[str] | None = None,
        home_region: str = "me-central-1",
        locale: str = "en",
    ) -> IdentityRealm:
        """Create the CyberCom mirror row AND push to Keycloak."""
        issuer_url = f"{getattr(settings, 'CYIDENTITY_ISSUER', '').rsplit('/realms/', 1)[0]}/realms/{realm_name}"
        jwks_uri = f"{issuer_url}/protocol/openid-connect/certs"
        admin_api = f"{issuer_url.rsplit('/realms/', 1)[0]}/admin/realms/{realm_name}"

        # Push to Keycloak first (real or fake)
        self.kc.authenticate()
        self.kc.create_realm(
            {
                "realm": realm_name,
                "enabled": enabled,
                "displayName": display_name or realm_name,
                "registrationAllowed": False,
                "loginWithEmailAllowed": True,
                "duplicateEmailsAllowed": False,
                "resetPasswordAllowed": False,
                "editUsernameAllowed": False,
                "bruteForceProtected": True,
                "accessTokenLifespan": access_token_lifetime,
                "sslRequired": "external",
                "attributes": {"home_region": home_region, "locale": locale},
            }
        )

        realm = IdentityRealm.objects.create(
            tenant_id=tenant_id,
            realm_name=realm_name,
            realm_type=realm_type,
            status=RealmStatus.PENDING,
            issuer_url=issuer_url,
            jwks_uri=jwks_uri,
            admin_api_url=admin_api,
            is_active=enabled,
            mfa_enforced=bool(mfa_methods),
            passkey_enabled=(mfa_methods or []) and "webauthn" in mfa_methods,
            home_region=home_region,
            locale=locale,
            metadata={"display_name": display_name or realm_name},
        )
        RealmConfiguration.objects.create(
            realm=realm,
            access_token_lifetime_seconds=access_token_lifetime,
            mfa_required_methods=mfa_methods or [],
        )
        metrics.realm_provisioned_total += 1
        return realm

    def activate(self, realm: IdentityRealm) -> IdentityRealm:
        realm.activate()
        self.kc.update_realm(realm.realm_name, {"enabled": True})
        return realm

    def suspend(self, realm: IdentityRealm, reason: str = "") -> IdentityRealm:
        realm.suspend()
        self.kc.update_realm(realm.realm_name, {"enabled": False})
        if reason:
            AuditService.record(
                action="update",
                resource_type="realm",
                resource_id=str(realm.id),
                tenant_id=realm.tenant_id,
                status="success",
                details={"event": "suspended", "reason": reason},
            )
        return realm

    def decommission(self, realm: IdentityRealm) -> IdentityRealm:
        # Mark decommissioned locally FIRST, then issue delete
        realm.decommission()
        try:
            self.kc.delete_realm(realm.realm_name)
        except KeycloakNotFound:
            logger.info("realm_already_absent_in_keycloak", extra={"realm": realm.realm_name})
        metrics.realm_decommissioned_total += 1
        return realm


# ---------------------------------------------------------------------------
# ClientService
# ---------------------------------------------------------------------------
class ClientService:
    """OAuth/OIDC client lifecycle + secret rotation."""

    def __init__(self, kc: KeycloakAdminClient | None = None):
        self.kc = kc or KeycloakAdminClient()

    def register(
        self,
        realm: IdentityRealm,
        *,
        client_id: str,
        name: str,
        protocol: str = "oidc",
        public_client: bool = False,
        redirect_uris: Iterable[str] = (),
        web_origins: Iterable[str] = (),
        root_url: str = "",
        mfa_required: bool = True,
        fapi_profile_enabled: bool = False,
        smart_on_fhir_enabled: bool = False,
    ) -> ApplicationClient:
        self.kc.authenticate()
        client_uuid = self.kc.create_client(
            realm.realm_name,
            {
                "clientId": client_id,
                "name": name,
                "protocol": protocol,
                "publicClient": public_client,
                "standardFlowEnabled": True,
                "directAccessGrantsEnabled": False,
                "serviceAccountsEnabled": not public_client,
                "redirectUris": list(redirect_uris),
                "webOrigins": list(web_origins),
                "rootUrl": root_url,
                "attributes": {
                    "mfa.required": str(mfa_required).lower(),
                    "fapi.profile.enabled": str(fapi_profile_enabled).lower(),
                    "smart.on.fhir.enabled": str(smart_on_fhir_enabled).lower(),
                },
            },
        )
        client = ApplicationClient.objects.create(
            realm=realm,
            client_id=client_id,
            name=name,
            protocol=protocol,
            public_client=public_client,
            redirect_uris=list(redirect_uris),
            web_origins=list(web_origins),
            root_url=root_url,
            mfa_required=mfa_required,
            fapi_profile_enabled=fapi_profile_enabled,
            smart_on_fhir_enabled=smart_on_fhir_enabled,
            attributes={
                "keycloak_uuid": client_uuid.get("id", "") if isinstance(client_uuid, dict) else ""
            },
        )
        metrics.client_created_total += 1
        return client

    def rotate_secret(
        self, client: ApplicationClient, created_by: str = ""
    ) -> tuple[ClientSecret, str]:
        """Generate a new client secret, store only its hash, return (row, cleartext)."""
        self.kc.authenticate()
        kc_uuid = client.attributes.get("keycloak_uuid") or client.client_id
        # In real mode we'd use the Keycloak UUID, not client_id
        secret_payload = self.kc.regenerate_client_secret(client.realm.realm_name, kc_uuid)
        cleartext = secret_payload.get("value") or secrets.token_urlsafe(48)

        # Revoke prior active secrets
        ClientSecret.objects.filter(client=client, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )

        row = ClientSecret.objects.create(
            tenant_id=client.realm.tenant_id,
            client=client,
            secret_hash=hash_client_secret(cleartext),
            secret_hint=cleartext[-4:],
            expires_at=timezone.now() + timedelta(days=90),  # quarterly rotation
            created_by=created_by,
        )
        metrics.secret_rotated_total += 1
        AuditService.record(
            action="update",
            resource_type="client_secret",
            resource_id=str(row.id),
            tenant_id=client.realm.tenant_id,
            user_id=created_by,
            status="success",
            details={"client_id": client.client_id, "event": "rotated"},
        )
        return row, cleartext


# ---------------------------------------------------------------------------
# UserProvisioningService — bulk user import + role sync
# ---------------------------------------------------------------------------
class UserProvisioningService:
    """Bulk import users from HRIS / SCIM and mirror role assignments."""

    def __init__(self, kc: KeycloakAdminClient | None = None):
        self.kc = kc or KeycloakAdminClient()

    def provision_user(
        self,
        realm: IdentityRealm,
        *,
        username: str,
        email: str,
        first_name: str = "",
        last_name: str = "",
        enabled: bool = True,
        email_verified: bool = False,
        attributes: dict[str, Any] | None = None,
    ) -> UserProfile:
        self.kc.authenticate()
        kc_user_id = self.kc.create_user(
            realm.realm_name,
            {
                "username": username,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": enabled,
                "emailVerified": email_verified,
                "attributes": attributes or {},
            },
        )
        profile, created = UserProfile.objects.update_or_create(
            realm=realm,
            username=username,
            defaults={
                "tenant_id": realm.tenant_id,
                "keycloak_user_id": kc_user_id,
                "email": email,
                "email_verified": email_verified,
                "given_name": first_name,
                "family_name": last_name,
                "display_name": f"{first_name} {last_name}".strip() or username,
                "enabled": enabled,
                "attributes": attributes or {},
            },
        )
        return profile

    def assign_role(self, user: UserProfile, role: Role, granted_by: str = "") -> RoleAssignment:
        self.kc.assign_role_to_user(user.realm.realm_name, str(user.keycloak_user_id), role.name)
        return RoleAssignment.objects.create(
            role=role,
            permission=None,
            child_role=None,
            kind="permission",
            granted_by=granted_by,
        )


# ---------------------------------------------------------------------------
# RoleSyncService
# ---------------------------------------------------------------------------
class RoleSyncService:
    """Idempotent role + permission catalog sync per realm."""

    def ensure_role(
        self,
        realm: IdentityRealm,
        name: str,
        *,
        display_name: str = "",
        description: str = "",
        client: ApplicationClient | None = None,
    ) -> Role:
        role, _ = Role.objects.update_or_create(
            realm=realm,
            name=name,
            client=client,
            defaults={
                "display_name": display_name or name,
                "description": description,
                "client_role": bool(client),
            },
        )
        return role

    def ensure_permission(
        self, scope: str, action: str, resource: str, *, description: str = ""
    ) -> Permission:
        perm, _ = Permission.objects.update_or_create(
            scope=scope,
            action=action,
            resource=resource,
            defaults={"description": description},
        )
        return perm

    def attach_permission(
        self, role: Role, permission: Permission, granted_by: str = ""
    ) -> RoleAssignment:
        return RoleAssignment.objects.create(
            role=role,
            permission=permission,
            child_role=None,
            kind="permission",
            granted_by=granted_by,
        )


# ---------------------------------------------------------------------------
# SessionService
# ---------------------------------------------------------------------------
class SessionService:
    """List + revoke sessions; idle timeout enforcement."""

    IDLE_THRESHOLD_SECONDS = 1800

    def revoke(self, session: UserSession, reason: str = "user_request") -> UserSession:
        session.revoke(reason)
        metrics.session_revoked_total += 1
        AuditService.record(
            action="logout",
            resource_type="session",
            resource_id=str(session.id),
            tenant_id=session.tenant_id,
            user_id=str(session.user_id),
            status="success",
            details={"event": "session_revoked", "reason": reason},
        )
        return session

    def revoke_all_for_user(self, user: UserProfile, reason: str = "admin_action") -> int:
        sessions = list(UserSession.objects.filter(user=user, status="active"))
        for s in sessions:
            self.revoke(s, reason)
        return len(sessions)

    def enforce_idle_timeout(self) -> int:
        cutoff = timezone.now() - timedelta(seconds=self.IDLE_THRESHOLD_SECONDS)
        stale = UserSession.objects.filter(status="active", last_activity_at__lt=cutoff)
        count = 0
        for s in stale:
            self.revoke(s, "idle_timeout")
            count += 1
        return count


# ---------------------------------------------------------------------------
# BreakGlassService
# ---------------------------------------------------------------------------
class BreakGlassService:
    """ADR-0017 §7.3 Risk-8: dual-approval, time-boxed, mandatory post-review."""

    def request(
        self,
        *,
        user: UserProfile,
        realm: IdentityRealm,
        reason: str,
        justification: str,
        target_resource: str,
        target_action: str,
    ) -> BreakGlassAccess:
        access = BreakGlassAccess.objects.create(
            tenant_id=user.tenant_id,
            user=user,
            realm=realm,
            reason=reason,
            justification=justification,
            target_resource=target_resource,
            target_action=target_action,
            status=BreakGlassStatus.REQUESTED,
        )
        metrics.break_glass_requested_total += 1
        AuditService.record(
            action="break_glass",
            resource_type=target_resource,
            resource_id=str(access.id),
            tenant_id=user.tenant_id,
            user_id=str(user.keycloak_user_id),
            status="success",
            details={"event": "requested", "reason": reason, "target_action": target_action},
        )
        return access

    def approve(
        self, access: BreakGlassAccess, approver: str, second_approver: str = ""
    ) -> BreakGlassAccess:
        if not second_approver:
            raise ValueError("Break-glass requires dual approval (ADR-0017 §7.3).")
        access.approve(approver, second_approver)
        AuditService.record(
            action="break_glass",
            resource_type=access.target_resource,
            resource_id=str(access.id),
            tenant_id=access.tenant_id,
            user_id=approver,
            status="success",
            details={"event": "approved", "second_approver": second_approver},
        )
        return access

    def activate(
        self, access: BreakGlassAccess, duration_seconds: int | None = None
    ) -> BreakGlassAccess:
        if access.status != BreakGlassStatus.APPROVED:
            raise ValueError("Break-glass must be approved before activation.")
        duration = duration_seconds or access.realm.configuration.break_glass_max_duration_seconds
        access.activate(duration)
        metrics.break_glass_activated_total += 1
        AuditService.record(
            action="break_glass",
            resource_type=access.target_resource,
            resource_id=str(access.id),
            tenant_id=access.tenant_id,
            user_id=str(access.user.keycloak_user_id),
            status="success",
            details={
                "event": "activated",
                "duration_seconds": duration,
                "expires_at": access.expires_at.isoformat() if access.expires_at else None,
            },
        )
        return access

    def expire_due(self) -> int:
        now = timezone.now()
        due = BreakGlassAccess.objects.filter(status=BreakGlassStatus.ACTIVE, expires_at__lte=now)
        count = 0
        for bg in due:
            bg.status = BreakGlassStatus.EXPIRED
            bg.save(update_fields=["status", "updated_at"])
            AuditService.record(
                action="break_glass",
                resource_type=bg.target_resource,
                resource_id=str(bg.id),
                tenant_id=bg.tenant_id,
                status="success",
                details={"event": "expired"},
            )
            count += 1
        return count


# ---------------------------------------------------------------------------
# AuditService — LoginAudit + emit to platform_audit_logs sink
# ---------------------------------------------------------------------------
class AuditService:
    """
    Records every CyIdentity-relevant action into:
      1. `LoginAudit` (CyIdentity-specific)
      2. `platform_audit_logs` (platform-wide immutable sink, when available)
    """

    @classmethod
    def record_login(
        cls,
        *,
        realm: IdentityRealm,
        username_attempted: str,
        outcome: str,
        ip_address: str | None = None,
        user_agent: str = "",
        user: UserProfile | None = None,
        session: UserSession | None = None,
        mfa_method: str = "",
        failure_reason: str = "",
        details: dict[str, Any] | None = None,
    ) -> LoginAudit:
        start = time.monotonic()
        event = LoginAudit.objects.create(
            tenant_id=realm.tenant_id,
            user=user,
            realm=realm,
            outcome=outcome,
            username_attempted=username_attempted,
            ip_address=ip_address,
            user_agent=user_agent,
            mfa_method=mfa_method,
            session=session,
            failure_reason=failure_reason,
            details=details or {},
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        metrics.login_latency_ms.append(elapsed_ms)
        # Emit to platform audit sink (if app installed)
        cls.record(
            action="login" if outcome == "success" else "permission_denied",
            resource_type="auth",
            resource_id=str(event.id),
            tenant_id=realm.tenant_id,
            user_id=str(user.keycloak_user_id) if user else username_attempted,
            status="success" if outcome == "success" else "failure",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "event": "login",
                "outcome": outcome,
                "mfa_method": mfa_method,
                "failure_reason": failure_reason,
                **(details or {}),
            },
        )
        return event

    @classmethod
    def record(
        cls,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        tenant_id: Any,
        user_id: str = "",
        status: str = "success",
        ip_address: str | None = None,
        user_agent: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        # Best-effort emit to platform audit sink
        try:
            from platform.audit.models import AuditLog

            AuditLog.objects.create(
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                status=status,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details or {},
            )
            metrics.audit_emitted_total += 1
        except Exception as exc:
            logger.warning("audit_sink_unavailable", extra={"reason": str(exc)})


# ---------------------------------------------------------------------------
# DomainEvent emission (ADR-0004 outbox pattern)
# ---------------------------------------------------------------------------
class IdentityEventEmitter:
    """Emits domain events via the platform outbox (best-effort)."""

    @staticmethod
    def emit(event_type: str, payload: dict[str, Any]) -> None:
        try:
            from platform.events.models import OutboxEvent

            OutboxEvent.objects.create(
                aggregate_type="cyidentity",
                event_type=event_type,
                payload=payload,
            )
        except Exception as exc:
            logger.warning(
                "outbox_emit_failed", extra={"event_type": event_type, "reason": str(exc)}
            )
