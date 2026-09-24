from django.db import models

from platform.common.models import BaseModel
from platform.common.slugs import unique_slugify


class ForumThread(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    body = models.TextField(blank=True)
    author_name = models.CharField(max_length=255, blank=True)
    author_email = models.EmailField(blank=True)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_forum_threads"
        unique_together = [("tenant_id", "slug")]
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(
                ForumThread.objects.filter(tenant_id=self.tenant_id), self.title, exclude_pk=self.pk
            )
        super().save(*args, **kwargs)


class ForumReply(BaseModel):
    thread = models.ForeignKey(ForumThread, related_name="replies", on_delete=models.CASCADE)
    body = models.TextField()
    author_name = models.CharField(max_length=255, blank=True)
    author_email = models.EmailField(blank=True)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_forum_replies"
        ordering = ["-is_accepted", "created_at"]

    def __str__(self):
        return f"Reply to {self.thread_id}"
