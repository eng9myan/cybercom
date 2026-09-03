"""3-way match tests (SQLite via settings_test)."""

import uuid
from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, Partner
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine
from products.cycom.procurement.services import three_way_match

T = uuid.uuid4()


class ThreeWayMatchTests(TestCase):
    def setUp(self):
        self.inv = Account.objects.create(tenant_id=T, code="1140", name="Inventory", account_type="asset")
        self.ap = Account.objects.create(tenant_id=T, code="2110", name="AP", account_type="liability")
        self.grni = Account.objects.create(tenant_id=T, code="2115", name="GRNI", account_type="liability")
        self.wh = Warehouse.objects.create(tenant_id=T, code="WH", name="Main")
        self.vendor = Partner.objects.create(tenant_id=T, name="Steel Co", partner_type="vendor")
        self.product = Product.objects.create(tenant_id=T, sku="RB", name="Rebar", inventory_account=self.inv)
        self.po = PurchaseOrder.objects.create(tenant_id=T, vendor=self.vendor, warehouse=self.wh, status="approved")
        # ordered 100 @ 5 = 500
        self.line = PurchaseOrderLine.objects.create(
            tenant_id=T, order=self.po, product=self.product,
            quantity=Decimal("100"), unit_cost=Decimal("5"), offset_account=self.grni,
        )

    def _bill(self, subtotal):
        return Invoice.objects.create(
            tenant_id=T, invoice_type="vendor", number=f"BILL-{subtotal}", partner=self.vendor,
            date=date.today(), due_date=date.today(), control_account=self.ap,
            amount_subtotal=Decimal(subtotal), amount_total=Decimal(subtotal), purchase_order=self.po,
        )

    def test_clean_match_full_receipt(self):
        self.line.quantity_received = Decimal("100"); self.line.save()  # received 500
        r = three_way_match(self._bill("500"))
        self.assertTrue(r["matched"])
        self.assertEqual(r["ordered"], Decimal("500.00"))
        self.assertEqual(r["received"], Decimal("500.00"))
        self.assertEqual(r["billed"], Decimal("500.00"))
        self.assertEqual(r["exceptions"], [])

    def test_bill_exceeds_received(self):
        self.line.quantity_received = Decimal("60"); self.line.save()  # received 300
        r = three_way_match(self._bill("500"))
        self.assertFalse(r["matched"])
        self.assertTrue(any("exceeds goods received" in e for e in r["exceptions"]))

    def test_partial_receipt_bill_within_received(self):
        self.line.quantity_received = Decimal("60"); self.line.save()  # received 300
        r = three_way_match(self._bill("300"))
        self.assertTrue(r["matched"])   # billed == received, ok
        self.assertTrue(any("Partial receipt" in e for e in r["exceptions"]))  # informational

    def test_unlinked_bill_raises(self):
        b = Invoice.objects.create(
            tenant_id=T, invoice_type="vendor", number="NOPO", partner=self.vendor,
            date=date.today(), due_date=date.today(), control_account=self.ap,
            amount_subtotal=Decimal("100"),
        )
        with self.assertRaises(ValidationError):
            three_way_match(b)
