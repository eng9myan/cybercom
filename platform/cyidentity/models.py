"""
CyIdentity platform models. ADR-0005: IAM strategy.
Stores realm/client configuration per tenant. Actual user directory lives in Keycloak/Zitadel.
"""
import uuid
from django.db import models
from platform.common.models import PlatformModel


class IdentityRealm(PlatformModel):
    """
    Maps a CyberCom tenant to its Keycloak/Zitadel realm.
    One realm per tenant (multi-realm model per ADR-0005).
    """
    tenant_id = models.UUIDField(unique=True, db_index=True)
    realm_name = models.CharField(max_length=100, unique=True)
    issuer_url = models.URLField(max_length=500)
    jwks_uri = models.URLField(max_length=500)
    client_id = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    mfa_enforced = models.BooleanField(default=True)
    passkey_enabled = models.BooleanField(default=True)
    saml_federation_enabled = models.BooleanField(default=False)
    scim_endpoint = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "platform_identity_realms"
        ordering = ["realm_name"]

    def __str__(self) -> str:
        return f"Realm({self.realm_name})"


class ServicePrincipal(PlatformModel):
    """
    Machine-to-machine service account. Issues short-lived mTLS/workload-OIDC tokens.
    ADR-0005: mTLS or workload-OIDC for services.
    """
    name = models.CharField(max_length=200)
    realm = models.ForeignKey(IdentityRealm, on_delete=models.PROTECT, related_name="service_principals")
    client_id = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    scopes = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "platform_service_principals"

    def __str__(self) -> str:
        return f"ServicePrincipal({self.name})"
