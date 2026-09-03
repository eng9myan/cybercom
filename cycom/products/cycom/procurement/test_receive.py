"""Procurement goods-receipt (partial + full) tests — SQLite via settings_test."""

import uuid
from decimal import Decimal

from django.test import TestCase

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.inventory.models import Product, StockItem, Warehouse
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine
from products.cycom.procurement.services import receive_purchase_order

TENANT = uuid.uuid4()


class GoodsReceiptTests(TestCase):
    def setUp(self):
        self.inv_acct = Account.objects.create(
            tenant_id=TENANT, code="1140", name="Inventory", account_type="asset"
        )
        self.grni = Account.objects.create(
            tenant_id=TENANT, code="2115", name="GRNI", account_type="liability"
        )
        self.wh = Warehouse.objects.create(tenant_id=TENANT, code="WH-MAIN", name="Main")
        self.vendor = Partner.objects.create(
            tenant_id=TENANT, name="Steel Supplier", partner_type="vendor"
        )
        self.product = Product.objects.create(
            tenant_id=TENANT, sku="RB-12", name="Rebar 12mm", inventory_account=self.inv_acct
        )
        self.po = PurchaseOrder.objects.create(
            tenant_id=TENANT, vendor=self.vendor, warehouse=self.wh, status="approved"
        )
        self.line = PurchaseOrderLine.objects.create(
            tenant_id=TENANT, order=self.po, product=self.product,
            quantity=Decimal("100"), unit_cost=Decimal("5"), offset_account=self.grni,
        )

    def _on_hand(self):
        si = StockItem.objects.filter(tenant_id=TENANT, product=self.product, warehouse=self.wh).first()
        return si.quantity_on_hand if si else Decimal("0")

    def test_partial_then_full_receipt(self):
        # Receive 60 of 100 -> partially_received, stock +60.
        receive_purchase_order(self.po, receipts={str(self.line.id): "60"})
        self.po.refresh_from_db(); self.line.refresh_from_db()
        self.assertEqual(self.po.status, "partially_received")
        self.assertEqual(self.line.quantity_received, Decimal("60"))
        self.assertEqual(self.line.quantity_remaining, Decimal("40"))
        self.assertEqual(self._on_hand(), Decimal("60"))

        # Receive the rest (full, no receipts arg) -> received, stock 100.
        receive_purchase_order(self.po)
        self.po.refresh_from_db(); self.line.refresh_from_db()
        self.assertEqual(self.po.status, "received")
        self.assertEqual(self.line.quantity_received, Decimal("100"))
        self.assertEqual(self._on_hand(), Decimal("100"))

    def test_over_receipt_capped_at_remaining(self):
        receive_purchase_order(self.po, receipts={str(self.line.id): "999"})
        self.line.refresh_from_db()
        self.assertEqual(self.line.quantity_received, Decimal("100"))  # capped
        self.assertEqual(self._on_hand(), Decimal("100"))

    def test_cannot_receive_unapproved(self):
        self.po.status = "draft"; self.po.save()
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            receive_purchase_order(self.po)
