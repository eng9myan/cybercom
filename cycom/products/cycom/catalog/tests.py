"""Catalog smoke tests — model creation + tenant scoping."""

import uuid

from django.test import TestCase

from products.cycom.catalog.models import Category, KitComponent, Product


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
