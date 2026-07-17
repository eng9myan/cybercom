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
