# S-3: catalog.Product is now the single product master. This migration
# repoints inventory's own FKs (StockItem, StockMove, InternalOrderLine) from
# inventory.Product to catalog.Product, then deletes inventory.Product itself
# — safe only once EVERY other app's FK has already been repointed (see the
# `dependencies` below: pos, sales, procurement, manufacturing, access all
# ran their own repoint migration first).

import django.db.models.deletion
from django.db import migrations, models


def repoint(apps, schema_editor):
    InventoryProduct = apps.get_model("cycom_inventory", "Product")
    CatalogProduct = apps.get_model("cycom_catalog", "Product")

    def _new_id(tenant_id, old_product_id):
        old = InventoryProduct.objects.get(pk=old_product_id)
        return CatalogProduct.objects.get(tenant_id=tenant_id, internal_ref=old.sku).id

    StockItem = apps.get_model("cycom_inventory", "StockItem")
    for item in StockItem.objects.all():
        item.product_new_id = _new_id(item.tenant_id, item.product_id)
        item.save(update_fields=["product_new"])

    StockMove = apps.get_model("cycom_inventory", "StockMove")
    for move in StockMove.objects.all():
        move.product_new_id = _new_id(move.tenant_id, move.product_id)
        move.save(update_fields=["product_new"])

    InternalOrderLine = apps.get_model("cycom_inventory", "InternalOrderLine")
    for line in InternalOrderLine.objects.all():
        line.product_new_id = _new_id(line.tenant_id, line.product_id)
        line.save(update_fields=["product_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('cycom_inventory', '0004_warehouse_pos_advance_liability_account_and_more'),
        ('cycom_catalog', '0003_product_inventory_account'),
        # every other app's FK must be repointed before Product can be deleted
        ('cycom_pos', '0007_posorderline_product_master'),
        ('cycom_sales', '0005_salesorderline_product_master'),
        ('cycom_procurement', '0003_product_master'),
        ('cycom_manufacturing', '0003_product_master'),
        ('cycom_access', '0003_accessgrant_product_master'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockitem', name='product_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='stock_items_new', to='cycom_catalog.product',
            ),
        ),
        migrations.AddField(
            model_name='stockmove', name='product_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='moves_new', to='cycom_catalog.product',
            ),
        ),
        migrations.AddField(
            model_name='internalorderline', name='product_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='internal_order_lines_new', to='cycom_catalog.product',
            ),
        ),
        migrations.RunPython(repoint, migrations.RunPython.noop),
        # StockItem.Meta.unique_together names 'product' — must drop the
        # constraint before RemoveField/RenameField can touch that field name.
        migrations.AlterUniqueTogether(name='stockitem', unique_together=set()),
        migrations.RemoveField(model_name='stockitem', name='product'),
        migrations.RenameField(model_name='stockitem', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='stockitem', name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='stock_items', to='cycom_catalog.product',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='stockitem', unique_together={('tenant_id', 'product', 'warehouse')},
        ),
        migrations.RemoveField(model_name='stockmove', name='product'),
        migrations.RenameField(model_name='stockmove', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='stockmove', name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='moves', to='cycom_catalog.product',
            ),
        ),
        migrations.RemoveField(model_name='internalorderline', name='product'),
        migrations.RenameField(model_name='internalorderline', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='internalorderline', name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='internal_order_lines', to='cycom_catalog.product',
            ),
        ),
        migrations.DeleteModel(name='Product'),
    ]
