# S-3: catalog.Product becomes the single product master (audit S-3). This
# migration (1) adds the inventory_account FK inventory.Product uniquely had,
# and (2) guarantees every existing inventory.Product has a matching
# catalog.Product row (same tenant, internal_ref == sku) before any other
# app's migration repoints its FK here — see products/cycom/inventory,
# pos, sales, procurement, manufacturing, access migrations that follow.

import django.db.models.deletion
from django.db import migrations, models


def ensure_catalog_coverage(apps, schema_editor):
    InventoryProduct = apps.get_model("cycom_inventory", "Product")
    CatalogProduct = apps.get_model("cycom_catalog", "Product")
    ProductUnit = apps.get_model("cycom_catalog", "ProductUnit")

    unit_cache = {}

    def _unit_for(tenant_id, uom):
        key = (tenant_id, uom)
        if key not in unit_cache:
            unit_cache[key], _ = ProductUnit.objects.get_or_create(
                tenant_id=tenant_id, abbreviation=uom, defaults={"name": uom.title() or uom},
            )
        return unit_cache[key]

    for inv_product in InventoryProduct.objects.all():
        catalog_product, created = CatalogProduct.objects.get_or_create(
            tenant_id=inv_product.tenant_id,
            internal_ref=inv_product.sku,
            defaults={
                "name": inv_product.name,
                "unit": _unit_for(inv_product.tenant_id, inv_product.uom),
                "inventory_account_id": inv_product.inventory_account_id,
                "is_active": inv_product.is_active,
            },
        )
        if not created and catalog_product.inventory_account_id is None:
            catalog_product.inventory_account_id = inv_product.inventory_account_id
            catalog_product.save(update_fields=["inventory_account"])


class Migration(migrations.Migration):

    dependencies = [
        ('cycom_catalog', '0002_category_attributes_category_created_by_and_more'),
        ('cycom_accounting', '0004_documentsequence'),
        ('cycom_inventory', '0004_warehouse_pos_advance_liability_account_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='inventory_account',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='catalog_products_as_inventory', to='cycom_accounting.account',
            ),
        ),
        migrations.RunPython(ensure_catalog_coverage, migrations.RunPython.noop),
    ]
