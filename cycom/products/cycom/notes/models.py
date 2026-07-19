from django.db import models

from platform.common.models import BaseModel


class Note(BaseModel):
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    owner = models.CharField(max_length=255, blank=True)
    tags = models.JSONField(default=list, blank=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_notes"
        ordering = ["-is_pinned", "-updated_at"]

    def __str__(self):
        return self.title or self.body[:40]
