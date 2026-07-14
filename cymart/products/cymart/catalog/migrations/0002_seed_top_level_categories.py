"""
Seeds the top-level category groups and a representative slice of children
from the CyberCom master spec section 10 examples. Not exhaustive — real
category management happens through the admin/API after this; this just
gives the taxonomy a real starting shape instead of an empty table.
"""

from django.db import migrations


SEED = {
    "food-and-restaurants": {
        "name_en": "Food & Restaurants",
        "children": {
            "arabic": "Arabic",
            "pizza": "Pizza",
            "burgers": "Burgers",
            "desserts": "Desserts",
            "bakeries": "Bakeries",
            "cafes": "Cafés",
            "asian": "Asian",
            "indian": "Indian",
            "healthy": "Healthy",
            "seafood": "Seafood",
            "fast-food": "Fast Food",
        },
    },
    "fashion": {
        "name_en": "Fashion",
        "children": {
            "fashion-men": "Men",
            "fashion-women": "Women",
            "fashion-children": "Children",
            "fashion-babies": "Babies",
            "shoes": "Shoes",
            "bags": "Bags",
            "accessories": "Accessories",
            "sportswear": "Sportswear",
        },
    },
    "retail": {
        "name_en": "Retail",
        "children": {
            "grocery": "Grocery",
            "electronics": "Electronics",
            "furniture": "Furniture",
            "cosmetics": "Cosmetics",
            "flowers": "Flowers",
            "books": "Books",
            "toys": "Toys",
            "baby-products": "Baby Products",
            "pet-supplies": "Pet Supplies",
            "hardware": "Hardware",
            "auto-parts": "Auto Parts",
            "medical-supplies": "Medical Supplies",
            "home-and-garden": "Home & Garden",
        },
    },
}

# Medical supplies is a real-world restricted category — flagged here as a
# concrete example of the healthcare-restriction fields actually being used,
# not just defined and left at defaults everywhere.
RESTRICTED_SLUGS = {"medical-supplies"}


def seed_categories(apps, schema_editor):
    Category = apps.get_model("cymart_catalog", "Category")
    for order, (root_slug, root_data) in enumerate(SEED.items()):
        if Category.objects.filter(slug=root_slug).exists():
            continue
        root = Category.objects.create(
            slug=root_slug, name_en=root_data["name_en"], display_order=order
        )
        for child_order, (child_slug, child_name) in enumerate(root_data["children"].items()):
            Category.objects.create(
                slug=child_slug,
                name_en=child_name,
                parent=root,
                display_order=child_order,
                is_restricted=child_slug in RESTRICTED_SLUGS,
                restriction_reason=(
                    "Requires pharmacy/medical-supply licensing verification"
                    if child_slug in RESTRICTED_SLUGS
                    else ""
                ),
            )


def remove_seeded_categories(apps, schema_editor):
    Category = apps.get_model("cymart_catalog", "Category")
    root_slugs = list(SEED.keys())
    child_slugs = [c for root in SEED.values() for c in root["children"]]
    # PROTECT on parent means children must go before their roots.
    Category.objects.filter(slug__in=child_slugs).delete()
    Category.objects.filter(slug__in=root_slugs).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("cymart_catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_seeded_categories),
    ]
