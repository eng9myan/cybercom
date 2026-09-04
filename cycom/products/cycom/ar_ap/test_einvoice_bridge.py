"""
The Invoice -> platform.einvoicing bridge (`run_einvoice_clearance`).

Verifies a posted customer invoice for a JO tenant gets cleared and the
result lands on the Invoice's einvoice_* fields, and that a non-JO tenant is
left untouched (einvoice_status stays "none").
"""
from datetime import date
from decimal import Decimal

import pytest

from platform.tenant.models import Tenant, TenantProfile
from products.cycom.accounting.models import Account
from products.cycom.ar_ap import einvoice as bridge
from products.cycom.ar_ap.models import Invoice, InvoiceLine, Partner


@pytest.fixture
def jo_tenant(db):
    t = Tenant.objects.create(name="Cafe Amman JO", slug="cafe-amman", country_code="JO")
    TenantProfile.objects.create(tenant=t, legal_name="Cafe Amman LLC", vat_number="200123456")
    return t


@pytest.fixture
def invoice_factory(db):
    def make(tenant_id, *, tax_pct="16"):
        ar = Account.objects.create(tenant_id=tenant_id, code="1100", name="AR", account_type="asset")
        rev = Account.objects.create(tenant_id=tenant_id, code="4000", name="Rev", account_type="income")
        tax = Account.objects.create(tenant_id=tenant_id, code="2120", name="VAT", account_type="liability")
        partner = Partner.objects.create(tenant_id=tenant_id, name="Walk-in", tax_id="")
        inv = Invoice.objects.create(
            tenant_id=tenant_id, invoice_type="customer", number="INV-1", partner=partner,
            date=date(2026, 7, 5), due_date=date(2026, 7, 20), currency="JOD",
            control_account=ar, tax_account=tax, status="posted",
        )
        InvoiceLine.objects.create(
            tenant_id=tenant_id, invoice=inv, account=rev, description="Latte",
            quantity=Decimal("3"), unit_price=Decimal("2.50"), tax_percent=Decimal(tax_pct),
        )
        return inv
    return make


@pytest.mark.django_db
def test_jo_invoice_is_cleared_via_engine(monkeypatch, jo_tenant, invoice_factory):
    class _FakeClient:
        def submit_invoice(self, xml, uuid):
            assert "PIH" in xml and "Latte" in xml
            return {"status": "submitted", "reference": "JO-0001", "qr": "QR==", "raw": {}}

    monkeypatch.setattr("platform.einvoicing.engine.JoFotaraClient", lambda *a, **k: _FakeClient())

    inv = invoice_factory(jo_tenant.id)
    bridge.run_einvoice_clearance(inv)
    inv.refresh_from_db()

    assert inv.einvoice_mode == "jo_jofotara"
    assert inv.einvoice_status == "cleared"
    assert inv.einvoice_icv == 1
    assert inv.einvoice_reference == "JO-0001"
    assert inv.einvoice_qr == "QR=="
    assert inv.einvoice_hash and inv.einvoice_uuid and inv.einvoice_cleared_at


@pytest.mark.django_db
def test_non_jo_tenant_is_left_untouched(db, invoice_factory):
    t = Tenant.objects.create(name="US Co", slug="us-co", country_code="US")
    inv = invoice_factory(t.id)
    bridge.run_einvoice_clearance(inv)
    inv.refresh_from_db()
    assert inv.einvoice_status == "none"
    assert inv.einvoice_mode == ""


@pytest.mark.django_db
def test_sa_tenant_routes_to_zatca(monkeypatch, db, invoice_factory):
    t = Tenant.objects.create(name="Riyadh Co", slug="riyadh-co", country_code="SA")
    TenantProfile.objects.create(tenant=t, legal_name="Riyadh Co LLC", vat_number="311111111100003")

    seen = {}

    class _FakeZatca:
        def submit(self, *, is_simplified, invoice_hash_b64, uuid, invoice_b64):
            seen["is_simplified"] = is_simplified
            return {"status": "reported" if is_simplified else "cleared",
                    "reference": "OK", "qr": "", "raw": {}}

    monkeypatch.setattr("platform.einvoicing.sa.client.ZatcaClient", lambda *a, **k: _FakeZatca())

    inv = invoice_factory(t.id)          # partner tax_id "" -> simplified B2C
    bridge.run_einvoice_clearance(inv)
    inv.refresh_from_db()
    assert inv.einvoice_mode == "sa_zatca"
    assert inv.einvoice_status == "reported"          # B2C simplified -> ZATCA reporting
    assert seen["is_simplified"] is True
    assert inv.einvoice_qr                            # TLV QR embedded


@pytest.mark.django_db
def test_engine_failure_marks_rejected_not_raise(monkeypatch, jo_tenant, invoice_factory):
    class _BadClient:
        def submit_invoice(self, xml, uuid):
            raise RuntimeError("sandbox down")

    monkeypatch.setattr("platform.einvoicing.engine.JoFotaraClient", lambda *a, **k: _BadClient())
    inv = invoice_factory(jo_tenant.id)
    bridge.run_einvoice_clearance(inv)   # must not raise
    inv.refresh_from_db()
    assert inv.einvoice_status == "rejected"
