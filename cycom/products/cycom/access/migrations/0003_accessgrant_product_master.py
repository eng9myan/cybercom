# S-3: repoint AccessGrant.product from inventory.Product (retired) to
# catalog.Product. See products/cycom/catalog/migrations/0003_product_inventory_account.py.

import django.db.models.deletion
from django.db import migrations, models


def repoint(apps, schema_editor):
    AccessGrant = apps.get_model("cycom_access", "AccessGrant")
    InventoryProduct = apps.get_model("cycom_inventory", "Product")
    CatalogProduct = apps.get_model("cycom_catalog", "Product")
    for grant in AccessGrant.objects.exclude(product__isnull=True):
        old = InventoryProduct.objects.get(pk=grant.product_id)
        new = CatalogProduct.objects.get(tenant_id=grant.tenant_id, internal_ref=old.sku)
        grant.product_new_id = new.id
        grant.save(update_fields=["product_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('cycom_access', '0002_accessgrant_attributes_accessgrant_created_by_and_more'),
        ('cycom_catalog', '0003_product_inventory_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='accessgrant', name='product_new',
            field=models.ForeignKey(
                null=True, blank=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='access_grants_new', to='cycom_catalog.product',
            ),
        ),
        migrations.RunPython(repoint, migrations.RunPython.noop),
        migrations.RemoveField(model_name='accessgrant', name='product'),
        migrations.RenameField(model_name='accessgrant', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='accessgrant', name='product',
            field=models.ForeignKey(
                null=True, blank=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='access_grants', to='cycom_catalog.product',
            ),
        ),
    ]
