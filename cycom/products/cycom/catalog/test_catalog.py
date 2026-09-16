"""Catalog smoke tests — model creation + tenant scoping."""

import uuid

from django.test import TestCase

from products.cycom.accounting.models import Account
from products.cycom.catalog.models import Category, KitComponent, Product, ProductUnit


class CatalogModelTests(TestCase):
    def setUp(self):
        self.tenant_id = uuid.uuid4()

    def test_category_slug_autofills(self):
        cat = Category.objects.create(tenant_id=self.tenant_id, name="Beverages")
        self.assertEqual(cat.slug, "beverages")

    def test_product_and_kit_bom(self):
        kit = Product.objects.create(
            tenant_id=self.tenant_id, name="Combo Meal", product_type="KIT"
        )
        part = Product.objects.create(tenant_id=self.tenant_id, name="Fries")
        line = KitComponent.objects.create(
            tenant_id=self.tenant_id,
            product=kit,
            component_product=part,
            quantity_per_unit="2.0000",
        )
        self.assertEqual(line.product, kit)
        self.assertEqual(kit.bom_components.count(), 1)

    def test_kit_component_rejects_self_reference(self):
        from django.core.exceptions import ValidationError

        p = Product.objects.create(tenant_id=self.tenant_id, name="X")
        with self.assertRaises(ValidationError):
            KitComponent.objects.create(
                tenant_id=self.tenant_id, product=p, component_product=p
            )


class ProductMasterMergeTests(TestCase):
    """S-3: catalog.Product absorbed inventory.Product (retired) as the single
    product master — it needs everything a stock-moving product requires
    (a GL inventory_account) alongside its existing merchandising fields, and
    the sku/uom compat properties that let code written against the old
    inventory.Product keep working unchanged."""

    def setUp(self):
        self.tenant_id = uuid.uuid4()
        self.inv_acct = Account.objects.create(
            tenant_id=self.tenant_id, code="1400", name="Inventory", account_type="asset"
        )

    def test_inventory_account_is_optional(self):
        # A SERVICE / non-stocked product legitimately has no GL inventory account.
        service = Product.objects.create(
            tenant_id=self.tenant_id, name="Consulting Hour", product_type="SERVICE"
        )
        self.assertIsNone(service.inventory_account)

    def test_stocked_product_carries_its_inventory_account(self):
        stocked = Product.objects.create(
            tenant_id=self.tenant_id, name="Widget", internal_ref="WID-1",
            product_type="STORABLE", inventory_account=self.inv_acct,
        )
        self.assertEqual(stocked.inventory_account, self.inv_acct)

    def test_sku_and_uom_compat_properties(self):
        kg = ProductUnit.objects.create(tenant_id=self.tenant_id, name="Kilogram", abbreviation="kg")
        p = Product.objects.create(
            tenant_id=self.tenant_id, name="Flour", internal_ref="FLR-1", unit=kg,
        )
        # Old inventory.Product code read `.sku` / `.uom` — same data, new names.
        self.assertEqual(p.sku, "FLR-1")
        self.assertEqual(p.uom, "kg")

    def test_uom_compat_property_blank_without_a_unit(self):
        p = Product.objects.create(tenant_id=self.tenant_id, name="No Unit Set")
        self.assertEqual(p.uom, "")
