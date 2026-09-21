from django.db import models

from platform.common.models import BaseModel


class Company(BaseModel):
    """A legal entity within a tenant. Multi-company is opt-in: every
    transactional model's `company` FK is nullable, so a single-company
    tenant that never creates one of these is completely unaffected —
    every existing query/report keeps working exactly as before."""

    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=10, default="JOD")
    parent_company = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="subsidiaries"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_companies"
        ordering = ["name"]

    def __str__(self):
        return self.name
