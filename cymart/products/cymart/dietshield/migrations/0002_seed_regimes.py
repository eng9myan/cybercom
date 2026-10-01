"""Seed the common diet regimes as data (rule packs). New diets are added
by inserting rows — no code change, no deploy."""

from django.db import migrations

REGIMES = [
    {
        "code": "keto",
        "name_en": "Keto",
        "name_ar": "كيتو",
        "description_en": "Very low carb, high fat.",
        "max_item_carbs_g": "15.0",
        "block_ingredients": ["sugar", "wheat", "rice", "potato", "corn", "bread"],
    },
    {
        "code": "gluten_free",
        "name_en": "Gluten-free",
        "name_ar": "خالٍ من الغلوتين",
        "block_ingredients": ["wheat", "barley", "rye", "malt", "bread", "pasta"],
    },
    {
        "code": "vegan",
        "name_en": "Vegan",
        "name_ar": "نباتي صرف",
        "block_ingredients": [
            "meat", "chicken", "beef", "lamb", "fish", "egg", "milk",
            "cheese", "butter", "honey", "cream",
        ],
    },
    {
        "code": "vegetarian",
        "name_en": "Vegetarian",
        "name_ar": "نباتي",
        "block_ingredients": ["meat", "chicken", "beef", "lamb", "fish", "shrimp"],
    },
    {
        "code": "halal",
        "name_en": "Halal",
        "name_ar": "حلال",
        "block_ingredients": ["pork", "bacon", "ham", "alcohol", "wine", "gelatin"],
    },
    {
        "code": "dairy_free",
        "name_en": "Dairy-free",
        "name_ar": "خالٍ من الألبان",
        "block_ingredients": ["milk", "cheese", "butter", "cream", "yogurt"],
    },
    {
        "code": "low_carb",
        "name_en": "Low-carb",
        "name_ar": "قليل الكربوهيدرات",
        "max_item_carbs_g": "40.0",
    },
]


def seed(apps, schema_editor):
    DietRegime = apps.get_model("cymart_dietshield", "DietRegime")
    for r in REGIMES:
        DietRegime.objects.update_or_create(code=r["code"], defaults=r)


def unseed(apps, schema_editor):
    DietRegime = apps.get_model("cymart_dietshield", "DietRegime")
    DietRegime.objects.filter(code__in=[r["code"] for r in REGIMES]).delete()


class Migration(migrations.Migration):
    dependencies = [("cymart_dietshield", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
