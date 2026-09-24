from django.db import models

from platform.common.models import BaseModel
from platform.common.slugs import unique_slugify

BLOCK_TYPE_CHOICES = [
    ("section", "Section"),
    ("columns", "Columns"),
    ("heading", "Heading"),
    ("text", "Text"),
    ("image", "Image"),
    ("button", "Button"),
    ("spacer", "Spacer"),
    ("video", "Video"),
    ("html", "Custom HTML"),
]

# Blocks that may contain other blocks (dropped into via the canvas).
# Deliberately one level deep — a child block cannot itself be a container —
# to keep the canvas's drop-target logic and the public renderer bounded.
CONTAINER_BLOCK_TYPES = {"section", "columns"}


class Page(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    is_published = models.BooleanField(default=False)
    is_homepage = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_cms_pages"
        unique_together = [("tenant_id", "slug")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                Page.objects.filter(tenant_id=self.tenant_id), self.title, exclude_pk=self.pk
            )
        super().save(*args, **kwargs)
        if self.is_homepage:
            # Only one homepage per tenant — demoting the others is cheaper
            # and less surprising than blocking the save with a validation
            # error the builder UI would have to specially handle.
            Page.objects.filter(tenant_id=self.tenant_id, is_homepage=True).exclude(pk=self.pk).update(
                is_homepage=False
            )


class PageBlock(BaseModel):
    page = models.ForeignKey(Page, related_name="blocks", on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", related_name="children", on_delete=models.CASCADE, null=True, blank=True
    )
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPE_CHOICES)
    order = models.PositiveIntegerField(default=0)
    # Type-specific props (text content, image_url/alt, button label/href,
    # heading level, spacer height, video url, raw html, background/padding
    # for containers). Never interpreted server-side beyond JSON validity —
    # the public renderer's block-type switch decides what each key means.
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cycom_cms_page_blocks"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.block_type} on {self.page_id}"
