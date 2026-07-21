from platform.tenant.models import Tenant

from products.cycom.localization.models import Jurisdiction


def get_jurisdiction_for_tenant(tenant_id) -> Jurisdiction | None:
    """Derives a tenant's billing jurisdiction from its own, already-real
    platform.tenant.Tenant.country_code — no new per-invoice field needed.
    Returns None if the tenant's country isn't in the seeded catalog yet
    (callers decide whether that's fatal or just skips compliance routing)."""
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return None
    return Jurisdiction.objects.filter(country_code=tenant.country_code).first()
