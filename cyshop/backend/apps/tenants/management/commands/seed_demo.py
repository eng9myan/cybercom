"""
Management command: python manage.py seed_demo

Creates a demo tenant and admin user so customers can explore CyShop
immediately without filling a registration form. Also seeds a real
owner workspace (company, two branches, warehouses, a product, opening
stock, and a demo device) so live-demo pages like Inter-Branch Transfers
and Device Registry have actual data instead of empty dropdowns.

Credentials:
  Workspace : demo
  Username  : demo
  Password  : Demo@cyshop1
  Email     : demo@cy-com.com

Owner login (used by the "Try the live demo" button on the login page):
  Username  : m.alnsour@outlook.com
  Password  : 12345678
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()

DEMO_TENANT = {
    "name": "CyShop Demo",
    "subdomain": "demo",
}

DEMO_ADMIN = {
    "username": "demo",
    "email": "demo@cy-com.com",
    "password": "Demo@cyshop1",
    "first_name": "Demo",
    "last_name": "User",
}

OWNER_ADMIN = {
    "username": "m.alnsour@outlook.com",
    "email": "m.alnsour@outlook.com",
    "password": "12345678",
    "first_name": "M",
    "last_name": "Alnsour",
}


class Command(BaseCommand):
    help = "Seed demo tenant, admin users, and a working owner workspace for live demonstrations"

    def handle(self, *args, **options):
        tenant = self._seed_tenant()
        self._seed_admin()
        self._seed_owner_admin(tenant)
        self._seed_owner_workspace(tenant)
        self.stdout.write(self.style.SUCCESS(
            "\nDemo ready!\n"
            f"  Workspace : {DEMO_TENANT['subdomain']}\n"
            f"  Username  : {DEMO_ADMIN['username']}\n"
            f"  Password  : {DEMO_ADMIN['password']}\n"
            f"  Owner     : {OWNER_ADMIN['username']} / {OWNER_ADMIN['password']}\n"
        ))

    def _seed_tenant(self):
        try:
            from apps.tenants.models import Tenant  # noqa: PLC0415
            tenant, created = Tenant.objects.get_or_create(
                subdomain=DEMO_TENANT["subdomain"],
                defaults={"name": DEMO_TENANT["name"]},
            )
            if created:
                self.stdout.write(f"  Created tenant: {tenant.name}")
            else:
                self.stdout.write(f"  Tenant already exists: {tenant.subdomain}")
            return tenant
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.WARNING(f"  Tenant seeding skipped: {exc}"))
            return None

    def _seed_admin(self):
        try:
            from apps.tenants.models import Tenant  # noqa: PLC0415
            tenant = Tenant.objects.get(subdomain=DEMO_TENANT["subdomain"])
        except Exception:  # noqa: BLE001
            tenant = None

        user, created = User.objects.get_or_create(
            username=DEMO_ADMIN["username"],
            defaults={
                "email": DEMO_ADMIN["email"],
                "first_name": DEMO_ADMIN["first_name"],
                "last_name": DEMO_ADMIN["last_name"],
                "is_staff": True,
                "is_superuser": False,
                "tenant_id": tenant.id if tenant else None,
            },
        )
        if created:
            user.set_password(DEMO_ADMIN["password"])
            user.save()
            self.stdout.write(f"  Created admin: {user.username}")
        else:
            # Always ensure tenant link is up to date
            if tenant and str(user.tenant_id) != str(tenant.id):
                user.tenant_id = tenant.id
                user.save()
                self.stdout.write(f"  Updated admin tenant link: {user.username} -> {tenant.subdomain}")
            else:
                self.stdout.write(f"  Admin already exists: {user.username}")

    def _seed_owner_admin(self, tenant):
        """
        Owner login used by the "Try the live demo" button on the login page.
        Password is force-reset on every deploy so it always matches OWNER_ADMIN,
        even if the account was previously created by hand with a different one.
        """
        user, created = User.objects.get_or_create(
            username=OWNER_ADMIN["username"],
            defaults={
                "email": OWNER_ADMIN["email"],
                "first_name": OWNER_ADMIN["first_name"],
                "last_name": OWNER_ADMIN["last_name"],
                "is_staff": True,
                "is_superuser": False,
                "tenant_id": tenant.id if tenant else None,
            },
        )
        if tenant and str(user.tenant_id) != str(tenant.id):
            user.tenant_id = tenant.id
        user.email = OWNER_ADMIN["email"]
        user.set_password(OWNER_ADMIN["password"])
        user.save()
        self.stdout.write(f"  {'Created' if created else 'Updated'} owner admin: {user.username}")

    def _seed_owner_workspace(self, tenant):
        """
        Company + two branches + warehouses/locations + a demo product + opening
        stock + a demo KDS device, so Inventory > Inter-Branch Transfers and
        Settings > Device Registry have real dropdown data to demo against.
        """
        if not tenant:
            return
        from apps.tenants.models import Company, Branch, TenantSettings  # noqa: PLC0415
        from apps.catalog.models import ProductUnit, TaxClass, Product  # noqa: PLC0415
        from apps.inventory.models import Warehouse, StockLocation, StockMovement  # noqa: PLC0415
        from apps.pos.models import Device  # noqa: PLC0415

        settings_obj, _ = TenantSettings.objects.get_or_create(tenant=tenant)
        if not settings_obj.onboarding_completed:
            settings_obj.onboarding_completed = True
            settings_obj.onboarding_step = 5
            settings_obj.save(update_fields=['onboarding_completed', 'onboarding_step', 'updated_at', 'version'])

        company, _ = Company.objects.get_or_create(
            tenant_id=tenant.id, name="CyShop Demo Co", defaults={"country_code": "JO"},
        )
        branch_a, _ = Branch.objects.get_or_create(
            tenant_id=tenant.id, company=company, name="Amman HQ",
            defaults={"address": "Amman, Jordan"},
        )
        branch_b, _ = Branch.objects.get_or_create(
            tenant_id=tenant.id, company=company, name="Riyadh Branch",
            defaults={"address": "Riyadh, Saudi Arabia"},
        )
        unit, _ = ProductUnit.objects.get_or_create(
            tenant_id=tenant.id, company=company, abbreviation="PCS", defaults={"name": "Piece"},
        )
        tax, _ = TaxClass.objects.get_or_create(
            tenant_id=tenant.id, company=company, code="STD",
            defaults={"name": "Standard", "rate": "0.1600"},
        )
        product, _ = Product.objects.get_or_create(
            tenant_id=tenant.id, company=company, internal_ref="DEMO-001",
            defaults={
                "name": "Demo Coffee Beans 1kg", "unit": unit, "tax_class": tax,
                "sell_price": "12.5000", "cost_price": "6.0000", "product_type": "STORABLE",
            },
        )
        wh_a, _ = Warehouse.objects.get_or_create(
            tenant_id=tenant.id, company=company, code="WH-AMM",
            defaults={"name": "Amman Warehouse", "branch": branch_a},
        )
        wh_b, _ = Warehouse.objects.get_or_create(
            tenant_id=tenant.id, company=company, code="WH-RUH",
            defaults={"name": "Riyadh Warehouse", "branch": branch_b},
        )
        loc_a, _ = StockLocation.objects.get_or_create(
            warehouse=wh_a, code="RCV",
            defaults={"name": "Receiving", "location_type": "RECEIVING", "tenant_id": tenant.id},
        )
        StockLocation.objects.get_or_create(
            warehouse=wh_b, code="RCV",
            defaults={"name": "Receiving", "location_type": "RECEIVING", "tenant_id": tenant.id},
        )
        if not StockMovement.objects.filter(
            tenant_id=tenant.id, product=product, to_location=loc_a, reference="SEED-OPENING"
        ).exists():
            StockMovement.objects.create(
                tenant_id=tenant.id, product=product, to_location=loc_a,
                quantity="100", movement_type="OPENING", reference="SEED-OPENING",
            )
        Device.objects.get_or_create(
            tenant_id=tenant.id, company=company, code="KDS-01",
            defaults={"name": "Kitchen Display 1", "branch": branch_a, "device_type": "KDS"},
        )
        self.stdout.write(f"  Owner workspace ready: {company.name} ({branch_a.name}, {branch_b.name})")
