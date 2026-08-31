"""Sales order lines + invoice bridge tests (SQLite via settings_test)."""

import uuid
from datetime import date
from decimal import Decimal

from django.test import TestCase

from products.cycom.accounting.models import Account
from products.cycom.accounting.services import post_journal_entry  # noqa: F401 (import sanity)
from products.cycom.ar_ap.views import InvoiceViewSet  # noqa: F401
from products.cycom.inventory.models import Product
from products.cycom.sales.models import SalesOrder, SalesOrderLine
from products.cycom.sales.services import create_invoice_from_order

T = uuid.uuid4()


class SalesFlowTests(TestCase):
    def setUp(self):
        self.ar = Account.objects.create(tenant_id=T, code="1130", name="AR", account_type="asset")
        self.inv = Account.objects.create(tenant_id=T, code="1140", name="Inventory", account_type="asset")
        self.tax = Account.objects.create(tenant_id=T, code="2120", name="Output GST", account_type="liability")
        self.rev = Account.objects.create(tenant_id=T, code="4100", name="Revenue", account_type="income")
        self.product = Product.objects.create(tenant_id=T, sku="RB-12", name="Rebar", inventory_account=self.inv)

        self.so = SalesOrder.objects.create(
            tenant_id=T, number="SO-1", customer_name="Ministry of Works",
            order_date=date.today(), status="draft",
        )
        SalesOrderLine.objects.create(tenant_id=T, order=self.so, product=self.product,
                                      quantity=Decimal("10"), unit_price=Decimal("100"), tax_percent=Decimal("16"))
        SalesOrderLine.objects.create(tenant_id=T, order=self.so, description="Delivery",
                                      quantity=Decimal("5"), unit_price=Decimal("50"), tax_percent=Decimal("16"))
        self.so.recompute_totals()

    def test_totals(self):
        self.so.refresh_from_db()
        self.assertEqual(self.so.amount_subtotal, Decimal("1250.00"))
        self.assertEqual(self.so.amount_tax, Decimal("200.00"))
        self.assertEqual(self.so.amount_total, Decimal("1450.00"))

    def test_line_discount(self):
        line = SalesOrderLine.objects.create(
            tenant_id=T, order=self.so, description="Discounted",
            quantity=Decimal("2"), unit_price=Decimal("100"), discount_percent=Decimal("10"), tax_percent=Decimal("16"),
        )
        self.assertEqual(line.subtotal, Decimal("180.00"))   # 200 - 10%
        self.assertEqual(line.tax_amount, Decimal("28.80"))

    def test_create_invoice_and_post_balances(self):
        self.so.status = "confirmed"
        self.so.save(update_fields=["status"])
        invoice = create_invoice_from_order(self.so)
        self.so.refresh_from_db()
        self.assertEqual(self.so.status, "invoiced")
        self.assertEqual(self.so.invoice_id, invoice.id)
        self.assertEqual(invoice.invoice_type, "customer")
        self.assertEqual(invoice.lines.count(), 2)
        self.assertEqual(invoice.partner.name, "Ministry of Works")

        # Post the invoice to the GL (existing service) and confirm it balances.
        from products.cycom.ar_ap.models import Invoice
        lines = list(invoice.lines.all())
        subtotal = sum((l.subtotal for l in lines), Decimal("0"))
        tax = sum((l.tax_amount for l in lines), Decimal("0"))
        gl = [{"account": invoice.control_account, "debit": subtotal + tax, "credit": 0}]
        for l in lines:
            gl.append({"account": l.account, "debit": 0, "credit": l.subtotal})
        gl.append({"account": invoice.tax_account, "debit": 0, "credit": tax})
        entry = post_journal_entry(tenant_id=T, date=date.today(), reference=invoice.number, lines=gl)
        self.assertEqual(entry.status, "posted")
        self.assertEqual(subtotal + tax, Decimal("1450.00"))

    def test_cannot_invoice_draft(self):
        from rest_framework.exceptions import ValidationError
        empty = SalesOrder.objects.create(tenant_id=T, number="SO-2", customer_name="X", order_date=date.today())
        with self.assertRaises(ValidationError):
            create_invoice_from_order(empty)  # no lines / not confirmed


class SalesQuotationFieldsTests(TestCase):
    """CyShop-ported quotation fields on SalesOrder: customer_type, valid_until, terms."""

    def test_defaults_and_wholesale(self):
        from datetime import timedelta

        so = SalesOrder.objects.create(
            tenant_id=T, number="Q-1", customer_name="Retail Walk-in",
            order_date=date.today(), status="draft",
        )
        self.assertEqual(so.customer_type, "retail")
        self.assertIsNone(so.valid_until)

        wholesale = SalesOrder.objects.create(
            tenant_id=T, number="Q-2", customer_name="Bulk Buyer LLC",
            order_date=date.today(), status="draft",
            customer_type="wholesale", valid_until=date.today() + timedelta(days=30),
            terms="Net 30. Prices valid 30 days.",
        )
        self.assertEqual(wholesale.customer_type, "wholesale")
        self.assertTrue(wholesale.valid_until > date.today())
