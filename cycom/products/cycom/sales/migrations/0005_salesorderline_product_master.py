# S-3: repoint SalesOrderLine.product from inventory.Product (retired) to
# catalog.Product. See products/cycom/catalog/migrations/0003_product_inventory_account.py.

import django.db.models.deletion
from django.db import migrations, models


def repoint(apps, schema_editor):
    SalesOrderLine = apps.get_model("cycom_sales", "SalesOrderLine")
    InventoryProduct = apps.get_model("cycom_inventory", "Product")
    CatalogProduct = apps.get_model("cycom_catalog", "Product")
    for line in SalesOrderLine.objects.exclude(product__isnull=True):
        old = InventoryProduct.objects.get(pk=line.product_id)
        new = CatalogProduct.objects.get(tenant_id=line.tenant_id, internal_ref=old.sku)
        line.product_new_id = new.id
        line.save(update_fields=["product_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('cycom_sales', '0004_salesorder_attributes_salesorder_created_by_and_more'),
        ('cycom_catalog', '0003_product_inventory_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesorderline', name='product_new',
            field=models.ForeignKey(
                null=True, blank=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='sales_order_lines_new', to='cycom_catalog.product',
            ),
        ),
        migrations.RunPython(repoint, migrations.RunPython.noop),
        migrations.RemoveField(model_name='salesorderline', name='product'),
        migrations.RenameField(model_name='salesorderline', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='salesorderline', name='product',
            field=models.ForeignKey(
                null=True, blank=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='sales_order_lines', to='cycom_catalog.product',
            ),
        ),
    ]
