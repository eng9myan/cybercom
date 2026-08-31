"""Smoke tests for the CyShop-ported Device + PosReceipt models."""

import uuid
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from products.cycom.accounting.models import Account
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.pos.models import Device, POSOrder, POSSession, PosReceipt

T = uuid.uuid4()


class DeviceTests(TestCase):
    def setUp(self):
        self.wh = Warehouse.objects.create(tenant_id=T, code="WH-1", name="Main")

    def test_route_property(self):
        kds = Device.objects.create(
            tenant_id=T, warehouse=self.wh, name="Kitchen 1", code="KDS-1", device_type="KDS"
        )
        self.assertEqual(kds.route, "/kds")

    def test_code_unique_per_tenant(self):
        Device.objects.create(tenant_id=T, name="A", code="DUP", device_type="POS")
        with self.assertRaises(IntegrityError):
            Device.objects.create(tenant_id=T, name="B", code="DUP", device_type="POS")


class PosReceiptTests(TestCase):
    def setUp(self):
        acc = lambda code, name, typ: Account.objects.create(
            tenant_id=T, code=code, name=name, account_type=typ
        )
        inv = acc("1200", "Inventory", "asset")
        cash = acc("1000", "Cash", "asset")
        rev = acc("4000", "Revenue", "income")
        cogs = acc("5000", "COGS", "expense")
        wh = Warehouse.objects.create(tenant_id=T, code="WH-R", name="R")
        session = POSSession.objects.create(tenant_id=T, warehouse=wh)
        self.order = POSOrder.objects.create(
            tenant_id=T, session=session, order_number="POS-1",
            cash_account=cash, revenue_account=rev, cogs_account=cogs,
        )

    def test_one_receipt_per_order(self):
        PosReceipt.objects.create(tenant_id=T, order=self.order, receipt_number="R-0001")
        self.assertEqual(self.order.receipt.receipt_number, "R-0001")

    def test_receipt_number_unique_per_tenant(self):
        PosReceipt.objects.create(tenant_id=T, order=self.order, receipt_number="R-DUP")
        wh2 = Warehouse.objects.create(tenant_id=T, code="WH-R2", name="R2")
        s2 = POSSession.objects.create(tenant_id=T, warehouse=wh2)
        cash = Account.objects.get(tenant_id=T, code="1000")
        rev = Account.objects.get(tenant_id=T, code="4000")
        cogs = Account.objects.get(tenant_id=T, code="5000")
        order2 = POSOrder.objects.create(
            tenant_id=T, session=s2, order_number="POS-2",
            cash_account=cash, revenue_account=rev, cogs_account=cogs,
        )
        with self.assertRaises(IntegrityError):
            PosReceipt.objects.create(tenant_id=T, order=order2, receipt_number="R-DUP")


class KitchenStatusTests(TestCase):
    def setUp(self):
        acc = lambda code, name, typ: Account.objects.create(
            tenant_id=T, code=code, name=name, account_type=typ
        )
        cash = acc("1000", "Cash", "asset")
        rev = acc("4000", "Revenue", "income")
        cogs = acc("5000", "COGS", "expense")
        wh = Warehouse.objects.create(tenant_id=T, code="WH-K", name="K")
        session = POSSession.objects.create(tenant_id=T, warehouse=wh)
        self.order = POSOrder.objects.create(
            tenant_id=T, session=session, order_number="POS-K1",
            source="KIOSK", table_ref="T7", customer_name="Walk-in",
            cash_account=cash, revenue_account=rev, cogs_account=cogs,
        )

    def test_defaults(self):
        self.assertEqual(self.order.kitchen_status, "pending")
        self.assertEqual(self.order.source, "KIOSK")
        self.assertEqual(self.order.table_ref, "T7")

    def test_advance_flow_and_stops_at_served(self):
        self.assertEqual(self.order.advance_kitchen(), "in_progress")
        self.assertEqual(self.order.advance_kitchen(), "ready")
        self.assertEqual(self.order.advance_kitchen(), "served")
        # No-op past the end.
        self.assertEqual(self.order.advance_kitchen(), "served")
