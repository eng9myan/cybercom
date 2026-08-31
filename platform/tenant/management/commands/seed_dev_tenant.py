"""
Seed the local-dev tenant so tenant-scoped writes pass isolation.

The fixed UUID here MUST match:
  - infrastructure/keycloak/cycom-dev-realm.json  (user attribute tenant_id -> token claim)
  - cycom-erp/.env.local                          (CYCOM_TENANT_ID)

Idempotent: safe to run repeatedly.

    python manage.py seed_dev_tenant
"""

import uuid

from django.core.management.base import BaseCommand

from platform.tenant.models import Tenant, TenantStatus, TenantType

DEV_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


class Command(BaseCommand):
    help = "Create/activate the fixed local-dev tenant (UUID 1111...1111)."

    def handle(self, *args, **options):
        tenant, created = Tenant.objects.get_or_create(
            id=DEV_TENANT_ID,
            defaults={
                "name": "Cycom Dev",
                "slug": "cycom-dev",
                "display_name": "Cycom Development Tenant",
                "tenant_type": TenantType.SAAS,
                "status": TenantStatus.ACTIVE,
                "country_code": "JO",
                "locale": "en",
            },
        )
        if not created and tenant.status != TenantStatus.ACTIVE:
            tenant.activate()

        verb = "Created" if created else "Ensured"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} dev tenant {tenant.name} ({tenant.id}) status={tenant.status}")
        )
