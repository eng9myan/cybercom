"""Seed a handful of common recipes so voice requests like 'stuff for
shakshuka' resolve to real ingredient lists. New recipes are added as
rows — no code change, no deploy."""

from django.db import migrations

RECIPES = [
    {
        "code": "shakshuka",
        "name_en": "Shakshuka",
        "name_ar": "شكشوكة",
        "servings": 2,
        "ingredients": [
            ("eggs", "6", "pcs"),
            ("tomato", "4", "pcs"),
            ("onion", "1", "pcs"),
            ("bell pepper", "1", "pcs"),
            ("garlic", "2", "cloves"),
            ("cumin", "1", "tsp"),
        ],
    },
    {
        "code": "greek_salad",
        "name_en": "Greek salad",
        "name_ar": "سلطة يونانية",
        "servings": 2,
        "ingredients": [
            ("cucumber", "1", "pcs"),
            ("tomato", "2", "pcs"),
            ("feta cheese", "150", "g"),
            ("olive", "50", "g"),
            ("olive oil", "2", "tbsp"),
        ],
    },
    {
        "code": "keto_chicken_bowl",
        "name_en": "Keto chicken bowl",
        "name_ar": "طبق دجاج كيتو",
        "servings": 2,
        "ingredients": [
            ("chicken breast", "400", "g"),
            ("spinach", "150", "g"),
            ("avocado", "1", "pcs"),
            ("olive oil", "2", "tbsp"),
        ],
    },
]


def seed(apps, schema_editor):
    Recipe = apps.get_model("cymart_pantry", "Recipe")
    RecipeIngredient = apps.get_model("cymart_pantry", "RecipeIngredient")
    for r in RECIPES:
        recipe, _ = Recipe.objects.update_or_create(
            code=r["code"],
            defaults={"name_en": r["name_en"], "name_ar": r["name_ar"], "servings": r["servings"]},
        )
        recipe.ingredients.all().delete()
        for name, qty, unit in r["ingredients"]:
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient_name=name, quantity=qty, unit=unit
            )


def unseed(apps, schema_editor):
    Recipe = apps.get_model("cymart_pantry", "Recipe")
    Recipe.objects.filter(code__in=[r["code"] for r in RECIPES]).delete()


class Migration(migrations.Migration):
    dependencies = [("cymart_pantry", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
