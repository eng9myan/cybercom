from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.tenants.models import Company, Tenant
from .models import Invoice, InvoiceLine, TaxProfile
from . import services


class _Ctx:
    def __init__(self, tid):
        self.tenant_id = tid


class EInvoiceTests(TestCase):
    def setUp(self):
        self.t = Tenant.objects.create(name="T", subdomain="t-einv")
        self.co = Company.objects.create(tenant_id=self.t.id, name="Acme", country_code="SA")

    def _invoice(self, **kw):
        inv = Invoice.objects.create(
            tenant_id=self.t.id, company=self.co, number=kw.get("number", "INV-1"),
            invoice_type="simplified", customer_name="Walk-in",
            issue_date=date(2026, 9, 1), currency="SAR")
        InvoiceLine.objects.create(tenant_id=self.t.id, invoice=inv, line_no=1,
                                   description="Widget", quantity=2, unit_price=25,
                                   tax_rate=Decimal("0.15"))
        inv.recalculate()
        return inv

    def test_totals(self):
        inv = self._invoice()
        self.assertEqual(inv.subtotal, Decimal("50.00"))
        self.assertEqual(inv.tax_total, Decimal("7.50"))
        self.assertEqual(inv.total, Decimal("57.50"))

    def test_generate_produces_xml_hash_qr(self):
        inv = self._invoice()
        doc = services.generate(inv)
        self.assertEqual(doc.status, "generated")
        self.assertTrue(doc.ubl_xml.startswith("<?xml"))
        self.assertIn("<cbc:TaxInclusiveAmount", doc.ubl_xml)
        self.assertTrue(doc.invoice_hash)
        self.assertTrue(doc.qr_code)          # base64 TLV
        # no scheme + no VAT -> two warnings, nothing submitted
        self.assertEqual(len(doc.warnings), 2)

    def test_submit_without_credentials_is_not_faked(self):
        inv = self._invoice()
        doc = services.generate(inv)
        doc = services.submit(doc)
        self.assertEqual(doc.status, "generated")   # not "submitted"
        self.assertTrue(any("portal" in w for w in doc.warnings))

    def test_hash_chain_advances(self):
        d1 = services.generate(self._invoice(number="A"))
        d2 = services.generate(self._invoice(number="B"))
        self.assertEqual(d2.pih, d1.invoice_hash)
        self.assertGreater(d2.icv, d1.icv)
