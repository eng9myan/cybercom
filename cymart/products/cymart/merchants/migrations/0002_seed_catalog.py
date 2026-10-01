"""Seeds 25 real Amman fast-food chains and 3 hypermarkets (HyperMax
real-scraped, Safeway duplicated from HyperMax, Cozmo hand-curated) —
see seed_data.py for provenance. Also creates a matching NutritionFact
row per product (source=ESTIMATED) so the diet shield, search_catalog,
and grocery-list features all have real data to work against."""

import uuid
from decimal import Decimal

from django.db import migrations

from products.cymart.merchants.seed_data import (
    COZMO_LOCATION,
    COZMO_PRODUCTS,
    HYPERMAX_LOCATION,
    HYPERMAX_PRODUCTS,
    RESTAURANTS,
    SAFEWAY_LOCATION,
)

# Rough per-item calorie/macro estimate by grocery category — groceries'
# useful shield signal is mainly diet_tags (regime gate); this keeps
# NutritionFact non-zero without pretending to precision the source site
# never published. All rows carry source=ESTIMATED, confidence=0.3.
GROCERY_MACROS = {
    "Dairy & Eggs": (150, 9, 4, 11),
    "Fruits & Vegetables": (60, 1, 14, 0),
    "Meat & Poultry": (220, 24, 1, 13),
    "Beverages": (60, 0, 14, 0),
    "Bakery": (260, 8, 46, 6),
    "Snacks": (560, 18, 20, 46),
    "Cooking essentials": (120, 0, 2, 13),
}
DEFAULT_MACROS = (150, 5, 15, 7)


def seed(apps, schema_editor):
    Merchant = apps.get_model("cymart_merchants", "Merchant")
    Product = apps.get_model("cymart_merchants", "Product")
    NutritionFact = apps.get_model("cymart_dietshield", "NutritionFact")

    def make_product(merchant, name, price, unit, category, diet_tags, ingredients,
                      calories, protein_g, carbs_g, fat_g, source_url=""):
        product = Product.objects.create(
            id=uuid.uuid4(), merchant=merchant, name=name, price=Decimal(str(price)),
            unit=unit, category=category, source_url=source_url,
        )
        NutritionFact.objects.create(
            id=uuid.uuid4(), product_id=product.id, name_snapshot=name,
            calories=Decimal(calories), protein_g=Decimal(protein_g),
            carbs_g=Decimal(carbs_g), fat_g=Decimal(fat_g),
            ingredients=ingredients, diet_tags=diet_tags + ["halal"],
            source="estimated", confidence=Decimal("0.6"),
        )
        return product

    # ── Restaurants ──────────────────────────────────────────────────
    for name, cuisine, (lat, lng), items in RESTAURANTS:
        merchant = Merchant.objects.create(
            id=uuid.uuid4(), tenant_id=uuid.uuid4(), name=name, kind="restaurant",
            cuisine=cuisine, city="Amman", lat=Decimal(str(lat)), lng=Decimal(str(lng)),
        )
        for item_name, price, kcal, protein, carbs, fat, tags, ingredients in items:
            make_product(
                merchant, item_name, price, "", cuisine, tags, ingredients,
                kcal, protein, carbs, fat,
            )

    # ── Hypermarkets ─────────────────────────────────────────────────
    def seed_grocery_merchant(name, coords, products, source_url=""):
        lat, lng = coords
        merchant = Merchant.objects.create(
            id=uuid.uuid4(), tenant_id=uuid.uuid4(), name=name, kind="hypermarket",
            cuisine="grocery", city="Amman", lat=Decimal(str(lat)), lng=Decimal(str(lng)),
            source_url=source_url,
        )
        for item_name, unit, price, category, tags in products:
            kcal, protein, carbs, fat = GROCERY_MACROS.get(category, DEFAULT_MACROS)
            make_product(
                merchant, item_name, price, unit, category, tags, [],
                kcal, protein, carbs, fat, source_url=source_url,
            )
        return merchant

    seed_grocery_merchant(
        "HyperMax", HYPERMAX_LOCATION, HYPERMAX_PRODUCTS,
        source_url="https://www.hypermax.com.jo/mafjor/en",
    )
    # Safeway has no Jordan storefront/website — duplicates HyperMax's
    # catalog at a different branch location, per instruction.
    seed_grocery_merchant("Safeway", SAFEWAY_LOCATION, HYPERMAX_PRODUCTS)
    seed_grocery_merchant(
        "Cozmo", COZMO_LOCATION, COZMO_PRODUCTS,
        source_url="https://www.thegroup.jo/cozmo-supermarket/",
    )


def unseed(apps, schema_editor):
    Merchant = apps.get_model("cymart_merchants", "Merchant")
    Product = apps.get_model("cymart_merchants", "Product")
    NutritionFact = apps.get_model("cymart_dietshield", "NutritionFact")
    # NutritionFact.product_id is a bare UUID, not a real FK (products
    # live outside dietshield by design) — clean it up explicitly before
    # the cascade removes the Product rows those ids point to.
    NutritionFact.objects.filter(
        product_id__in=list(Product.objects.values_list("id", flat=True))
    ).delete()
    Merchant.objects.all().delete()  # cascades to Product


class Migration(migrations.Migration):
    dependencies = [
        ("cymart_merchants", "0001_initial"),
        ("cymart_dietshield", "0002_seed_regimes"),
    ]
    operations = [migrations.RunPython(seed, unseed)]
