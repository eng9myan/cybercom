# S-3: repoint BillOfMaterial.product and BOMComponent.component from
# inventory.Product (retired) to catalog.Product. See
# products/cycom/catalog/migrations/0003_product_inventory_account.py.
# Also fixes BillOfMaterial's ordering, which referenced the retired
# inventory.Product.sku field directly (catalog.Product's real field is
# internal_ref; `sku` is a Python-only compat property, not a DB column).

import django.db.models.deletion
from django.db import migrations, models


def repoint(apps, schema_editor):
    InventoryProduct = apps.get_model("cycom_inventory", "Product")
    CatalogProduct = apps.get_model("cycom_catalog", "Product")

    def _new_id(tenant_id, old_product_id):
        old = InventoryProduct.objects.get(pk=old_product_id)
        return CatalogProduct.objects.get(tenant_id=tenant_id, internal_ref=old.sku).id

    BillOfMaterial = apps.get_model("cycom_manufacturing", "BillOfMaterial")
    for bom in BillOfMaterial.objects.all():
        bom.product_new_id = _new_id(bom.tenant_id, bom.product_id)
        bom.save(update_fields=["product_new"])

    BOMComponent = apps.get_model("cycom_manufacturing", "BOMComponent")
    for comp in BOMComponent.objects.all():
        comp.component_new_id = _new_id(comp.tenant_id, comp.component_id)
        comp.save(update_fields=["component_new"])


class Migration(migrations.Migration):

    dependencies = [
        ('cycom_manufacturing', '0002_billofmaterial_attributes_billofmaterial_created_by_and_more'),
        ('cycom_catalog', '0003_product_inventory_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='billofmaterial', name='product_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='boms_new', to='cycom_catalog.product',
            ),
        ),
        migrations.AddField(
            model_name='bomcomponent', name='component_new',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name='used_in_boms_new', to='cycom_catalog.product',
            ),
        ),
        migrations.RunPython(repoint, migrations.RunPython.noop),
        migrations.RemoveField(model_name='billofmaterial', name='product'),
        migrations.RenameField(model_name='billofmaterial', old_name='product_new', new_name='product'),
        migrations.AlterField(
            model_name='billofmaterial', name='product',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='boms', to='cycom_catalog.product',
            ),
        ),
        migrations.RemoveField(model_name='bomcomponent', name='component'),
        migrations.RenameField(model_name='bomcomponent', old_name='component_new', new_name='component'),
        migrations.AlterField(
            model_name='bomcomponent', name='component',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='used_in_boms', to='cycom_catalog.product',
            ),
        ),
        migrations.AlterModelOptions(
            name='billofmaterial',
            options={'ordering': ['product__internal_ref', 'name']},
        ),
    ]
