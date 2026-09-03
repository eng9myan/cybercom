"""Phase-1 proof: exercise the real self-serve provisioning path in-process.

Uses Django's test Client so we hit the ACTUAL URLconf -> serializer ->
DemoProvisioningService / SubscriptionRegistrationService -> DB, exactly like a
real HTTP request, then exit. No long-running server needed.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_dev")
os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("CYCOM_DEV_AUTH", "1")
django.setup()

import json
from django.test import Client

c = Client()

def show(title, resp):
    print(f"\n=== {title} -> HTTP {resp.status_code} ===")
    try:
        print(json.dumps(resp.json(), indent=2, default=str)[:1200])
    except Exception:
        print(resp.content[:600])

# 1) Demo (72h trial) for the ERP product
show("DEMO cycom (retail)", c.post(
    "/api/v1/tenants/demo/",
    data=json.dumps({"product_code": "cycom", "email": "trial@demo.test",
                     "org_name": "Phase1 Cafe", "locale": "ar"}),
    content_type="application/json"))

# 2) Register (permanent + invoice) — the payment SEAM (no card yet)
show("REGISTER cycom Pro", c.post(
    "/api/v1/tenants/register/",
    data=json.dumps({"product_code": "cycom", "tier": "professional",
                     "email": "buyer@demo.test", "org_name": "Phase1 Retail Co",
                     "locale": "ar"}),
    content_type="application/json"))

# 3) Hospital must be BLOCKED from self-serve (sales-assisted only)
show("DEMO cymed_hospital (should be blocked)", c.post(
    "/api/v1/tenants/demo/",
    data=json.dumps({"product_code": "cymed_hospital", "email": "hosp@demo.test",
                     "org_name": "Test Hospital"}),
    content_type="application/json"))

show("REGISTER cymed_hospital (should be blocked)", c.post(
    "/api/v1/tenants/register/",
    data=json.dumps({"product_code": "cymed_hospital", "tier": "professional",
                     "email": "hosp2@demo.test", "org_name": "Test Hospital 2"}),
    content_type="application/json"))

# Summary of what landed in the DB
from platform.tenant.models import Tenant
from products.cycom.subscriptions.models import Subscription
print("\n=== DB STATE ===")
print("tenants:", Tenant.objects.count())
for t in Tenant.objects.order_by("-created_at")[:5]:
    print(f"  - {t.slug} status={t.status} name={t.name}")
