from django.db import models

from platform.common.models import BaseModel


class Article(BaseModel):
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    tags = models.JSONField(default=list, blank=True)
    author = models.CharField(max_length=255, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_knowledge_articles"
        ordering = ["title"]

    def __str__(self):
        return self.title
