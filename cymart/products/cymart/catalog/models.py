import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    """
    CyMart's own hierarchical category taxonomy (master spec section 10).
    Lives in CyMart's database — CyShop/CyCom stores reference these by ID
    (see their Branch.marketplace_category_ids / pos.config.
    marketplace_category_ids soft-reference fields) rather than a real FK,
    since they're separate deployable services with separate databases.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )

    slug = models.SlugField(max_length=140, unique=True)
    name_en = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    description_en = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    image_url = models.URLField(blank=True)

    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    # Arbitrary category-specific attributes/filters (e.g. {"cuisine": [...],
    # "dietary": [...]}) — schema varies per category, hence JSON not columns.
    attributes = models.JSONField(default=dict, blank=True)
    filters = models.JSONField(default=list, blank=True)

    # Restricted-product / eligibility policy
    is_restricted = models.BooleanField(default=False)
    restriction_reason = models.CharField(max_length=300, blank=True)
    # Empty list = eligible everywhere. Non-empty = allow-list of ISO 3166-1
    # alpha-2 country codes.
    allowed_country_codes = models.JSONField(default=list, blank=True)
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    requires_prescription = models.BooleanField(default=False)
    is_controlled_substance = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymart_category"
        ordering = ["display_order", "name_en"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name_en

    def clean(self):
        # Unlimited depth is fine, but a category can't be its own ancestor.
        node = self.parent
        while node is not None:
            if node.pk == self.pk:
                raise ValidationError("A category cannot be its own ancestor.")
            node = node.parent

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def ancestors(self) -> list["Category"]:
        result = []
        node = self.parent
        while node is not None:
            result.append(node)
            node = node.parent
        return list(reversed(result))

    def descendants(self) -> list["Category"]:
        result = []
        for child in self.children.all():
            result.append(child)
            result.extend(child.descendants())
        return result

    @property
    def full_path(self) -> str:
        return " / ".join([a.name_en for a in self.ancestors()] + [self.name_en])

    def is_eligible_for_country(self, country_code: str) -> bool:
        if not self.allowed_country_codes:
            return True
        return country_code in self.allowed_country_codes
