# S-3: repoint POSOrderLine.product from inventory.Product (retired) to
# catalog.Product, the new single product master. See
# products/cycom/catalog/migrations/0003_product_inventory_account.py for the
# coverage guarantee this depends on (every inventory.Product has a matching
# catalog.Product, same tenant, internal_ref == sku).

import django.db.models.deletion
from django.db import migrations, models


def repoint(apps, schema_editor):
    POSOrderLine = apps.get_model("cycom_pos", "POSOrderLine")
    InventoryProduct = apps.get_model("cycom_inventory", "Product")
    CatalogProduct = apps.get_model("cycom_catalog", "Product")
    for line in POSOrderLine.objects.all():
        old = InventoryProduct.objects.get(pk=line.product_id)
        new = CatalogProduct.objects.get(tenant_id=line.tenant_id, internal_ref=old.sku)
        line.product_new_id = new.id
        line.save(update_fields=["product_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('cycom_pos', '0006_device_attributes_device_created_by_and_more'),
        ('cycom_catalog', '0003_product_inventory_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='posorderline', name='product_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='pos_order_lines_new', to='cycom_catalog.product',
            ),
        ),
        migrations.RunPython(repoint, migrations.RunPython.noop),
        migrations.RemoveField(model_name='posorderline', name='product'),
        migrations.RenameField(model_name='posorderline', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='posorderline', name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pos_order_lines', to='cycom_catalog.product',
            ),
        ),
    ]
