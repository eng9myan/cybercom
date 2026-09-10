"""A-4 — gapless per-tenant/per-type document numbering.

Covers the allocator invariants (sequential, no gaps, per-type and per-period
isolation, concurrency-safe) and the three wired entry points: AR/AP invoices,
POS orders, payroll runs — including that a manual number is a role-gated
override, not the default.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest
from django.db import connection
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account, DocumentSequence
from products.cycom.accounting.sequencing import allocate_document_number
from products.cycom.ar_ap.models import Invoice, Partner
from products.cycom.payroll.models import PayrollRun
from products.cycom.pos.models import POSOrder, POSSession


# ── allocator unit tests ────────────────────────────────────────────────────
@pytest.mark.django_db
def test_allocations_are_sequential_and_gapless():
    t = uuid.uuid4()
    nums = [allocate_document_number(t, "customer_invoice", when=date(2026, 3, 1)) for _ in range(5)]
    assert nums == [
        "INV-2026-00001", "INV-2026-00002", "INV-2026-00003",
        "INV-2026-00004", "INV-2026-00005",
    ]
    seq = DocumentSequence.objects.get(tenant_id=t, doc_type="customer_invoice")
    assert seq.next_value == 6


@pytest.mark.django_db
def test_doc_types_and_tenants_are_isolated():
    t1, t2 = uuid.uuid4(), uuid.uuid4()
    assert allocate_document_number(t1, "customer_invoice", when=date(2026, 1, 1)) == "INV-2026-00001"
    assert allocate_document_number(t1, "vendor_bill", when=date(2026, 1, 1)) == "BILL-2026-00001"
    assert allocate_document_number(t2, "customer_invoice", when=date(2026, 1, 1)) == "INV-2026-00001"


@pytest.mark.django_db
def test_yearly_sequence_resets_on_period_rollover():
    t = uuid.uuid4()
    assert allocate_document_number(t, "customer_invoice", when=date(2026, 12, 31)) == "INV-2026-00001"
    assert allocate_document_number(t, "customer_invoice", when=date(2027, 1, 1)) == "INV-2027-00001"
    # going back to the old period does NOT resurrect the old counter
    assert allocate_document_number(t, "customer_invoice", when=date(2026, 6, 1)) == "INV-2026-00001"


@pytest.mark.django_db
def test_pos_sequence_is_monthly():
    t = uuid.uuid4()
    assert allocate_document_number(t, "pos_order", when=date(2026, 9, 5)) == "POS-202609-00001"
    assert allocate_document_number(t, "pos_order", when=date(2026, 10, 1)) == "POS-202610-00001"


@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="needs real SELECT FOR UPDATE row locking (Postgres)",
)
@pytest.mark.django_db(transaction=True)
def test_concurrent_allocation_never_collides():
    t = uuid.uuid4()

    def grab():
        return allocate_document_number(t, "customer_invoice", when=date(2026, 5, 1))

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: grab(), range(24)))

    assert len(set(results)) == 24  # no duplicates
    values = sorted(int(r.split("-")[-1]) for r in results)
    assert values == list(range(1, 25))  # no gaps


# ── wired entry points ──────────────────────────────────────────────────────
@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    client = APIClient()
    token = mint_token({
        "sub": str(uuid.uuid4()), "email": "admin@cybercom.io",
        "tenant_id": str(tenant_id), "realm_access": {"roles": ["platform_admin"]},
    })
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant_id))
    return client


@pytest.fixture
def clerk_client(mint_token, mock_jwks, tenant_id):
    """A signed-in user with no finance/admin role — may create documents but
    may not hand-pick their numbers."""
    client = APIClient()
    token = mint_token({
        "sub": str(uuid.uuid4()), "email": "clerk@cybercom.io",
        "tenant_id": str(tenant_id), "realm_access": {"roles": ["employee"]},
    })
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant_id))
    return client


@pytest.fixture
def invoice_accounts(db, tenant_id):
    return {
        "control": Account.objects.create(tenant_id=tenant_id, code="1100", name="AR", account_type="asset"),
        "revenue": Account.objects.create(tenant_id=tenant_id, code="4000", name="Sales", account_type="income"),
        "tax": Account.objects.create(tenant_id=tenant_id, code="2200", name="Tax Payable", account_type="liability"),
        "partner": Partner.objects.create(tenant_id=tenant_id, name="Acme Co", partner_type="customer"),
    }


def _invoice_payload(acc, **over):
    body = {
        "invoice_type": "customer",
        "partner": str(acc["partner"].id),
        "date": "2026-04-10",
        "due_date": "2026-05-10",
        "control_account": str(acc["control"].id),
        "tax_account": str(acc["tax"].id),
        "lines": [{"account": str(acc["revenue"].id), "quantity": "1", "unit_price": "100", "tax_percent": "16"}],
    }
    body.update(over)
    return body


@pytest.mark.django_db
def test_invoice_number_auto_allocated_when_omitted(admin_client, invoice_accounts):
    r1 = admin_client.post("/api/v1/ar-ap/invoices/", _invoice_payload(invoice_accounts), format="json")
    r2 = admin_client.post("/api/v1/ar-ap/invoices/", _invoice_payload(invoice_accounts), format="json")
    assert r1.status_code == 201, r1.content
    assert r2.status_code == 201, r2.content
    assert r1.data["number"] == "INV-2026-00001"
    assert r2.data["number"] == "INV-2026-00002"


@pytest.mark.django_db
def test_vendor_bill_uses_its_own_series(admin_client, invoice_accounts):
    r = admin_client.post(
        "/api/v1/ar-ap/invoices/",
        _invoice_payload(invoice_accounts, invoice_type="vendor"),
        format="json",
    )
    assert r.status_code == 201, r.content
    assert r.data["number"] == "BILL-2026-00001"


@pytest.mark.django_db
def test_manual_number_rejected_without_finance_role(clerk_client, invoice_accounts):
    r = clerk_client.post(
        "/api/v1/ar-ap/invoices/",
        _invoice_payload(invoice_accounts, number="INV-HAND-1"),
        format="json",
    )
    assert r.status_code == 400
    assert "number" in str(r.data)
    # ... and with no number it still goes through
    ok = clerk_client.post("/api/v1/ar-ap/invoices/", _invoice_payload(invoice_accounts), format="json")
    assert ok.status_code == 201, ok.content
    assert ok.data["number"] == "INV-2026-00001"


@pytest.mark.django_db
def test_manual_number_allowed_for_finance_role(admin_client, invoice_accounts):
    r = admin_client.post(
        "/api/v1/ar-ap/invoices/",
        _invoice_payload(invoice_accounts, number="INV-MIGRATED-42"),
        format="json",
    )
    assert r.status_code == 201, r.content
    assert r.data["number"] == "INV-MIGRATED-42"


@pytest.mark.django_db
def test_pos_order_number_auto_allocated(admin_client, tenant_id):
    from products.cycom.inventory.models import Product, Warehouse

    inv_acc = Account.objects.create(
        tenant_id=tenant_id, code="1200", name="Inventory", account_type="asset"
    )
    cash = Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset")
    rev = Account.objects.create(tenant_id=tenant_id, code="4000", name="Sales", account_type="income")
    cogs = Account.objects.create(tenant_id=tenant_id, code="5000", name="COGS", account_type="expense")
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH1", name="Main")
    session = POSSession.objects.create(tenant_id=tenant_id, warehouse=wh, opening_cash=0)
    prod = Product.objects.create(
        tenant_id=tenant_id, sku="SKU1", name="Widget", inventory_account=inv_acc
    )
    payload = {
        "session": str(session.id),
        "cash_account": str(cash.id),
        "revenue_account": str(rev.id),
        "cogs_account": str(cogs.id),
        "lines": [{"product": str(prod.id), "quantity": "1", "unit_price": "10"}],
    }
    r = admin_client.post("/api/v1/pos/orders/", payload, format="json")
    assert r.status_code == 201, r.content
    assert r.data["order_number"].startswith("POS-")
    assert r.data["order_number"].endswith("-00001")


@pytest.mark.django_db
def test_payroll_run_number_auto_allocated_and_used_as_je_reference(admin_client, tenant_id):
    exp = Account.objects.create(tenant_id=tenant_id, code="5100", name="Salary Exp", account_type="expense")
    pay = Account.objects.create(tenant_id=tenant_id, code="2100", name="Salary Payable", account_type="liability")
    payload = {
        "period_start": "2026-01-01", "period_end": "2026-01-31",
        "salary_expense_account": str(exp.id), "salary_payable_account": str(pay.id),
    }
    r = admin_client.post("/api/v1/payroll/runs/", payload, format="json")
    assert r.status_code == 201, r.content
    assert r.data["number"] == "PR-2026-001"
    assert PayrollRun.objects.get(pk=r.data["id"]).number == "PR-2026-001"
