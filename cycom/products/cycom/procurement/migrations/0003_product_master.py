# S-3: repoint PurchaseRequestLine.product and PurchaseOrderLine.product from
# inventory.Product (retired) to catalog.Product. See
# products/cycom/catalog/migrations/0003_product_inventory_account.py.

import django.db.models.deletion
from django.db import migrations, models


def repoint(apps, schema_editor):
    InventoryProduct = apps.get_model("cycom_inventory", "Product")
    CatalogProduct = apps.get_model("cycom_catalog", "Product")

    def _new_id(tenant_id, old_product_id):
        old = InventoryProduct.objects.get(pk=old_product_id)
        return CatalogProduct.objects.get(tenant_id=tenant_id, internal_ref=old.sku).id

    PurchaseRequestLine = apps.get_model("cycom_procurement", "PurchaseRequestLine")
    for line in PurchaseRequestLine.objects.all():
        line.product_new_id = _new_id(line.tenant_id, line.product_id)
        line.save(update_fields=["product_new"])

    PurchaseOrderLine = apps.get_model("cycom_procurement", "PurchaseOrderLine")
    for line in PurchaseOrderLine.objects.all():
        line.product_new_id = _new_id(line.tenant_id, line.product_id)
        line.save(update_fields=["product_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('cycom_procurement', '0002_purchaseorder_attributes_purchaseorder_created_by_and_more'),
        ('cycom_catalog', '0003_product_inventory_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchaserequestline', name='product_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='purchase_request_lines_new', to='cycom_catalog.product',
            ),
        ),
        migrations.AddField(
            model_name='purchaseorderline', name='product_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='purchase_order_lines_new', to='cycom_catalog.product',
            ),
        ),
        migrations.RunPython(repoint, migrations.RunPython.noop),
        migrations.RemoveField(model_name='purchaserequestline', name='product'),
        migrations.RenameField(model_name='purchaserequestline', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='purchaserequestline', name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='purchase_request_lines', to='cycom_catalog.product',
            ),
        ),
        migrations.RemoveField(model_name='purchaseorderline', name='product'),
        migrations.RenameField(model_name='purchaseorderline', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='purchaseorderline', name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='purchase_order_lines', to='cycom_catalog.product',
            ),
        ),
    ]
