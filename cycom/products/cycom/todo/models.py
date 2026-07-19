from django.db import models

from platform.common.models import BaseModel


class Task(BaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(null=True, blank=True)
    linked_model = models.CharField(max_length=100, blank=True)
    linked_id = models.UUIDField(null=True, blank=True)
    is_done = models.BooleanField(default=False)
    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_todo_tasks"
        ordering = ["is_done", "due_date"]

    def __str__(self):
        return self.title
