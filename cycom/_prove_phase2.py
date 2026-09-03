"""Phase-2 proof: provider-agnostic online-payment seam.

Run twice:
  CYCOM_PAYMENT_PROVIDER=manual  -> register returns bank-transfer instructions,
                                    priced in the resolved currency; tenant PENDING.
  CYCOM_PAYMENT_PROVIDER=fake     -> register returns a redirect checkout; the
                                    simulate endpoint completes payment and the
                                    tenant flips ACTIVE via the single path.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_dev")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("CYCOM_DEV_AUTH", "1")
django.setup()

import json
from django.conf import settings
from django.test import Client

c = Client()
prov = getattr(settings, "PAYMENT_PROVIDER", "manual")
print(f"\n########## ACTIVE PROVIDER = {prov} ##########")

def j(resp):
    try:
        return resp.json()
    except Exception:
        return resp.content[:400]

# Public pricing config (website pricing page)
pc = c.get("/api/v1/tenants/pricing/")
print("\n=== GET /pricing/ ->", pc.status_code, "===")
print(json.dumps(j(pc), indent=2)[:900])

# Register — currency resolved from country=JO -> JOD
r = c.post("/api/v1/tenants/register/",
           data=json.dumps({"product_code": "cycom", "tier": "professional",
                            "email": f"buyer.{prov}@demo.test",
                            "org_name": f"P2 {prov} Co", "country": "JO"}),
           content_type="application/json")
print("\n=== POST /register/ ->", r.status_code, "===")
body = j(r)
print(json.dumps(body, indent=2, default=str)[:1100])

from platform.tenant.models import Tenant, TenantSubscriptionInvoice, InvoiceStatus
inv_no = body.get("invoice_number")
tenant = Tenant.objects.get(slug=body["tenant_slug"])
print(f"\nAfter register: tenant.status={tenant.status}  invoice.status={TenantSubscriptionInvoice.objects.get(invoice_number=inv_no).status}")

if prov == "fake":
    sim = c.get(f"/api/v1/tenants/payments/simulate/?invoice={inv_no}")
    print("\n=== GET /payments/simulate/ ->", sim.status_code, "===")
    print(json.dumps(j(sim), indent=2, default=str)[:500])
    tenant.refresh_from_db()
    inv = TenantSubscriptionInvoice.objects.get(invoice_number=inv_no)
    print(f"\nAfter payment: tenant.status={tenant.status}  invoice.status={inv.status}  sub.is_active={inv.subscription.is_active}")
    assert tenant.status == "active" and inv.status == InvoiceStatus.PAID, "ONLINE PAYMENT DID NOT ACTIVATE"
    print("ONLINE PAYMENT LOOP: PASS")
