from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from platform.common.models import BaseModel


class BlogPost(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    excerpt = models.TextField(blank=True)
    content = models.TextField(blank=True)
    author_name = models.CharField(max_length=255, blank=True)
    cover_image_url = models.URLField(max_length=500, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_blog_posts"
        unique_together = [("tenant_id", "slug")]
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
