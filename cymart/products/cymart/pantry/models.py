import uuid

from django.db import models


class PurchaseSource(models.TextChoices):
    ORDER = "order", "Order checkout"
    MANUAL = "manual", "Manually logged"


class PurchaseHistory(models.Model):
    """An append-only log of what a customer bought and when — the raw
    signal ReplenishEngine learns a consumption rate from. Populated
    automatically at cart checkout (see cart.services.CartService) and
    optionally by a manual "I bought this elsewhere" log."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField(db_index=True)
    product_name_snapshot = models.CharField(max_length=300, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, blank=True)
    purchased_at = models.DateField()
    source = models.CharField(
        max_length=10, choices=PurchaseSource.choices, default=PurchaseSource.ORDER
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymart_purchase_history"
        indexes = [models.Index(fields=["customer_id", "product_id", "purchased_at"])]
        ordering = ["-purchased_at"]

    def __str__(self):
        return f"{self.quantity}x {self.product_name_snapshot or self.product_id} ({self.purchased_at})"


class PantryItem(models.Model):
    """The learned, running state for one customer+product: when it was
    last bought, how often it's typically re-bought, and when it's
    predicted to run out. Updated every time ReplenishEngine.record_
    purchase() logs a new PurchaseHistory row."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField()
    product_name_snapshot = models.CharField(max_length=300, blank=True)
    unit = models.CharField(max_length=20, blank=True)

    last_purchased_at = models.DateField(null=True, blank=True)
    last_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # Rolling-average days between purchases. Null until a second purchase
    # gives us a first interval to learn from.
    typical_interval_days = models.PositiveSmallIntegerField(null=True, blank=True)
    predicted_runout_date = models.DateField(null=True, blank=True)

    is_tracked = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_pantry_item"
        constraints = [
            models.UniqueConstraint(
                fields=["customer_id", "product_id"], name="unique_pantry_item_per_customer"
            )
        ]
        ordering = ["predicted_runout_date"]

    def __str__(self):
        return f"PantryItem({self.product_name_snapshot or self.product_id})"


class Recipe(models.Model):
    """A data-driven recipe → ingredient list, so a voice request like
    'stuff for shakshuka' resolves to real SKUs via RecipeResolver +
    GroceryListBuilder. New recipes are added as rows, no deploy."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=60, unique=True)
    name_en = models.CharField(max_length=150)
    name_ar = models.CharField(max_length=150, blank=True)
    servings = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymart_recipe"
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en


class RecipeIngredient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    # Lowercased free-text token matched against NutritionFact.name_snapshot
    # / ingredients — recipes aren't tied to specific SKUs, so this is
    # resolved at list-build time the same way NutritionResolver works.
    ingredient_name = models.CharField(max_length=120)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "cymart_recipe_ingredient"

    def __str__(self):
        return f"{self.quantity}{self.unit} {self.ingredient_name}"
