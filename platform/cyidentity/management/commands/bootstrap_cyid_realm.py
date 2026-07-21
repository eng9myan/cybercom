"""
One-time (idempotent) bootstrap of the shared "cyid" Keycloak realm — the
CyID ecosystem's home realm (see docs: CyID ecosystem plan, Phase 2).

Every person who enrolls in CyID (`CyIDService.enroll`) gets exactly one
UserProfile here; visiting a new tenant for the first time links an
additional UserProfile in that tenant's own realm back to the same
PersonIdentity (`CyIDService.link_tenant_profile`). The client registered
here is deliberately public (no secret) with direct password grants
enabled — the software-token MVP's whole point is "know the password" as
proof of identity, checked live against this realm, no secret needed.

Idempotent against BOTH the local DB mirror rows AND Keycloak directly,
same discipline as `bootstrap_platform_realm`.

Usage:
    python manage.py bootstrap_cyid_realm
"""

from __future__ import annotations

import uuid

from django.core.management.base import BaseCommand, CommandError

from platform.cyidentity.models import ApplicationClient, IdentityRealm, RealmStatus, RealmType
from platform.cyidentity.services import ClientService, KeycloakAdminClient, RealmService

REALM_NAME = "cyid"
CLIENT_ID = "cyid-home"


class Command(BaseCommand):
    help = "Bootstrap the shared 'cyid' Keycloak realm and its public home client."

    def handle(self, *args, **options):
        kc = KeycloakAdminClient()
        kc.authenticate()

        realm = IdentityRealm.objects.filter(realm_name=REALM_NAME).first()
        if realm:
            self.stdout.write(f"Realm '{REALM_NAME}' already has a local row (id={realm.id}) — reusing it.")
        else:
            sentinel_tenant_id = uuid.uuid5(uuid.NAMESPACE_URL, f"platform-realm:{REALM_NAME}")
            try:
                realm = RealmService().provision(
                    tenant_id=sentinel_tenant_id,
                    realm_name=REALM_NAME,
                    realm_type=RealmType.CITIZEN,
                    display_name="CyberCom CyID",
                )
                RealmService().activate(realm)
                self.stdout.write(self.style.SUCCESS(f"Created realm '{REALM_NAME}' in Keycloak + DB."))
            except Exception as exc:
                if "already exists" not in str(exc).lower():
                    raise CommandError(f"Realm provisioning failed: {exc}") from exc
                issuer_base = kc.base_url
                issuer_url = f"{issuer_base}/realms/{REALM_NAME}"
                realm = IdentityRealm.objects.create(
                    tenant_id=sentinel_tenant_id,
                    realm_name=REALM_NAME,
                    realm_type=RealmType.CITIZEN,
                    status=RealmStatus.ACTIVE,
                    issuer_url=issuer_url,
                    jwks_uri=f"{issuer_url}/protocol/openid-connect/certs",
                    admin_api_url=f"{issuer_base}/admin/realms/{REALM_NAME}",
                    is_active=True,
                    metadata={"display_name": "CyberCom CyID", "adopted_existing": True},
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"Realm '{REALM_NAME}' already existed in Keycloak — created local mirror row only."
                    )
                )

        client = realm.clients.filter(client_id=CLIENT_ID).first()
        if not client:
            existing_kc_client = kc.find_client_by_client_id(REALM_NAME, CLIENT_ID)
            if existing_kc_client:
                client = ApplicationClient.objects.create(
                    realm=realm,
                    client_id=CLIENT_ID,
                    name="CyID Home",
                    protocol="openid-connect",
                    public_client=True,
                    direct_access_grants_enabled=True,
                    mfa_required=False,
                    attributes={"keycloak_uuid": existing_kc_client.get("id", ""), "adopted_existing": True},
                )
                self.stdout.write(
                    self.style.WARNING(f"Client '{CLIENT_ID}' already existed in Keycloak — adopted it.")
                )
            else:
                client = ClientService().register(
                    realm,
                    client_id=CLIENT_ID,
                    name="CyID Home",
                    public_client=True,
                    direct_access_grants_enabled=True,
                    mfa_required=False,
                    cyid_claims_enabled=True,
                )
                self.stdout.write(self.style.SUCCESS(f"Created client '{CLIENT_ID}' with CyID claim mappers."))
        else:
            self.stdout.write(f"Client '{CLIENT_ID}' already has a local row — reusing it.")

        self.stdout.write(self.style.SUCCESS("\nCyID home realm bootstrap complete."))
        self.stdout.write(f"  Realm:      {REALM_NAME}")
        self.stdout.write(f"  Client ID:  {CLIENT_ID} (public, direct-access-grants enabled)")
        self.stdout.write(
            "  Next: enroll a person via POST /api/v1/identity/persons/enroll/, "
            "then link them into a tenant realm's client (register that client with "
            "cyid_claims_enabled=True too) via POST /api/v1/identity/persons/{id}/link-tenant/."
        )
