"""
One-time (idempotent) bootstrap of the shared "cybercom" Keycloak realm.

Nothing in the codebase creates a stable, non-per-tenant realm — only
DemoProvisioningService creates one realm PER demo signup. This command
creates the one shared realm that real (non-demo) logins, the admin panel,
and any backend-to-backend auth need: a realm, an OIDC client on it, and a
real platform-admin user with the `platform_admin` role so IsPlatformAdmin
checks pass.

Idempotent against BOTH the local DB mirror rows AND Keycloak directly —
re-running this is safe even if a prior run (or an unrelated earlier
session) already created the realm/client/user straight in Keycloak without
a matching local row.

Usage:
    python manage.py bootstrap_platform_realm --admin-email you@cy-com.com
"""

from __future__ import annotations

import secrets
import uuid

from django.core.management.base import BaseCommand, CommandError

from platform.cyidentity.models import ApplicationClient, IdentityRealm, RealmStatus, RealmType, UserProfile
from platform.cyidentity.services import (
    ClientService,
    KeycloakAdminClient,
    RealmService,
    UserProvisioningService,
)

REALM_NAME = "cybercom"
CLIENT_ID = "cybercom-backend"
ADMIN_ROLE = "platform_admin"


class Command(BaseCommand):
    help = "Bootstrap the shared 'cybercom' Keycloak realm, OIDC client, and a platform-admin user."

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-email", required=True, help="Email for the platform-admin user to create."
        )
        parser.add_argument(
            "--admin-username", default="platform-admin", help="Username for the admin user."
        )

    def handle(self, *args, **options):
        admin_email = options["admin_email"]
        admin_username = options["admin_username"]
        kc = KeycloakAdminClient()
        kc.authenticate()

        # --- Realm -------------------------------------------------------------
        realm = IdentityRealm.objects.filter(realm_name=REALM_NAME).first()
        if realm:
            self.stdout.write(f"Realm '{REALM_NAME}' already has a local row (id={realm.id}) — reusing it.")
        else:
            sentinel_tenant_id = uuid.uuid5(uuid.NAMESPACE_URL, f"platform-realm:{REALM_NAME}")
            try:
                realm = RealmService().provision(
                    tenant_id=sentinel_tenant_id,
                    realm_name=REALM_NAME,
                    realm_type=RealmType.WORKFORCE,
                    display_name="CyberCom Platform",
                )
                RealmService().activate(realm)
                self.stdout.write(self.style.SUCCESS(f"Created realm '{REALM_NAME}' in Keycloak + DB."))
            except Exception as exc:
                if "already exists" not in str(exc).lower():
                    raise CommandError(f"Realm provisioning failed: {exc}") from exc
                # Realm exists in Keycloak already (e.g. an earlier session
                # created it directly) but has no local mirror row — build one
                # without re-pushing to Keycloak.
                issuer_base = kc.base_url
                issuer_url = f"{issuer_base}/realms/{REALM_NAME}"
                realm = IdentityRealm.objects.create(
                    tenant_id=sentinel_tenant_id,
                    realm_name=REALM_NAME,
                    realm_type=RealmType.WORKFORCE,
                    status=RealmStatus.ACTIVE,
                    issuer_url=issuer_url,
                    jwks_uri=f"{issuer_url}/protocol/openid-connect/certs",
                    admin_api_url=f"{issuer_base}/admin/realms/{REALM_NAME}",
                    is_active=True,
                    metadata={"display_name": "CyberCom Platform", "adopted_existing": True},
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"Realm '{REALM_NAME}' already existed in Keycloak — created local mirror row only."
                    )
                )

        # --- OIDC client ---------------------------------------------------------
        client = realm.clients.filter(client_id=CLIENT_ID).first()
        if not client:
            existing_kc_client = kc.find_client_by_client_id(REALM_NAME, CLIENT_ID)
            if existing_kc_client:
                client = ApplicationClient.objects.create(
                    realm=realm,
                    client_id=CLIENT_ID,
                    name="CyberCom Backend",
                    protocol="oidc",
                    public_client=False,
                    mfa_required=False,
                    direct_access_grants_enabled=True,
                    attributes={"keycloak_uuid": existing_kc_client.get("id", ""), "adopted_existing": True},
                )
                self.stdout.write(
                    self.style.WARNING(f"Client '{CLIENT_ID}' already existed in Keycloak — adopted it.")
                )
                # Adopted client may not have direct_access_grants enabled —
                # fix that so password-grant verification works.
                import httpx  # type: ignore

                httpx.put(
                    f"{kc.base_url}/admin/realms/{REALM_NAME}/clients/{existing_kc_client['id']}",
                    json={**existing_kc_client, "directAccessGrantsEnabled": True},
                    headers=kc._auth_headers(),
                    timeout=kc.timeout_seconds,
                )
            else:
                client = ClientService().register(
                    realm,
                    client_id=CLIENT_ID,
                    name="CyberCom Backend",
                    public_client=False,
                    direct_access_grants_enabled=True,
                    mfa_required=False,
                )
                self.stdout.write(self.style.SUCCESS(f"Created client '{CLIENT_ID}'."))
        else:
            self.stdout.write(f"Client '{CLIENT_ID}' already has a local row — reusing it.")
        _secret_row, cleartext_secret = ClientService().rotate_secret(
            client, created_by="bootstrap_command"
        )

        # --- tenant_id in the token (both halves must be true) -------------------
        # Self-serve / demo signups on this shared realm set tenant_id as a
        # Keycloak user *attribute* (SubscriptionRegistrationService /
        # DemoProvisioningService). For that to reach the issued access token:
        #   (1) the realm must accept unmanaged attributes, or Keycloak's User
        #       Profile schema silently drops tenant_id on save; and
        #   (2) the client needs an oidc-usermodel-attribute-mapper exposing
        #       that attribute as the tenant_id claim in the access token.
        # RealmService.provision()/ClientService.register() do both for
        # freshly-created per-tenant realms, but this command's realm/client
        # are frequently *adopted* from a pre-existing Keycloak install, which
        # bypasses those paths. Enforce both here, idempotently.
        kc.allow_unmanaged_user_attributes(REALM_NAME)

        import httpx  # type: ignore

        kc_client_uuid = client.attributes.get("keycloak_uuid") or (
            (kc.find_client_by_client_id(REALM_NAME, CLIENT_ID) or {}).get("id", "")
        )
        if kc_client_uuid:
            mappers_url = (
                f"{kc.base_url}/admin/realms/{REALM_NAME}"
                f"/clients/{kc_client_uuid}/protocol-mappers/models"
            )
            existing = httpx.get(
                mappers_url, headers=kc._auth_headers(), timeout=kc.timeout_seconds
            )
            has_tenant_mapper = existing.status_code < 400 and any(
                m.get("config", {}).get("user.attribute") == "tenant_id"
                and m.get("config", {}).get("claim.name") == "tenant_id"
                for m in existing.json()
            )
            if not has_tenant_mapper:
                kc.create_protocol_mapper(
                    REALM_NAME,
                    kc_client_uuid,
                    {
                        "name": "tenant-id-mapper",
                        "protocol": "openid-connect",
                        "protocolMapper": "oidc-usermodel-attribute-mapper",
                        "consentRequired": False,
                        "config": {
                            "user.attribute": "tenant_id",
                            "claim.name": "tenant_id",
                            "jsonType.label": "String",
                            "id.token.claim": "true",
                            "access.token.claim": "true",
                            "userinfo.token.claim": "true",
                            "introspection.token.claim": "true",
                        },
                    },
                )
                self.stdout.write(self.style.SUCCESS("Added tenant_id protocol mapper to client."))
            else:
                self.stdout.write("tenant_id protocol mapper already present — reusing it.")

        # --- Platform-admin role -------------------------------------------------
        kc.create_realm_role(REALM_NAME, ADMIN_ROLE)

        # --- Platform-admin user --------------------------------------------------
        user = UserProfile.objects.filter(realm=realm, username=admin_username).first()
        password = secrets.token_urlsafe(16)
        if user:
            self.stdout.write(f"User '{admin_username}' already has a local row — resetting password + role.")
            kc.set_user_password(REALM_NAME, str(user.keycloak_user_id), password, temporary=False)
            kc.assign_role_to_user(REALM_NAME, str(user.keycloak_user_id), ADMIN_ROLE)
        else:
            existing_kc_user = kc.find_user_by_username(REALM_NAME, admin_username)
            if existing_kc_user:
                user = UserProfile.objects.create(
                    realm=realm,
                    tenant_id=realm.tenant_id,
                    username=admin_username,
                    keycloak_user_id=existing_kc_user["id"],
                    email=existing_kc_user.get("email", admin_email),
                    display_name=admin_username,
                    enabled=True,
                    attributes={"role": ["platform_admin"], "adopted_existing": True},
                )
                kc.set_user_password(REALM_NAME, str(user.keycloak_user_id), password, temporary=False)
                kc.assign_role_to_user(REALM_NAME, str(user.keycloak_user_id), ADMIN_ROLE)
                self.stdout.write(
                    self.style.WARNING(f"User '{admin_username}' already existed in Keycloak — adopted it.")
                )
            else:
                user = UserProvisioningService().provision_user(
                    realm,
                    username=admin_username,
                    email=admin_email,
                    first_name="Platform",
                    last_name="Admin",
                    enabled=True,
                    email_verified=True,
                    attributes={"role": ["platform_admin"]},
                    password=password,
                )
                kc.assign_role_to_user(REALM_NAME, str(user.keycloak_user_id), ADMIN_ROLE)
                self.stdout.write(self.style.SUCCESS(f"Created platform-admin user '{admin_username}'."))

        self.stdout.write(self.style.SUCCESS("\nBootstrap complete. Save these now — not stored anywhere:"))
        self.stdout.write(f"  Realm:            {REALM_NAME}")
        self.stdout.write(f"  Client ID:        {CLIENT_ID}")
        self.stdout.write(f"  Client secret:    {cleartext_secret}")
        self.stdout.write(f"  Admin username:   {admin_username}")
        self.stdout.write(f"  Admin password:   {password}")
