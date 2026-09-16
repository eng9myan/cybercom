from django.db import models

from platform.common.models import BaseModel


class Visitor(BaseModel):
    full_name = models.CharField(max_length=255)
    organisation = models.CharField(max_length=255, blank=True)
    purpose = models.CharField(max_length=255, blank=True)
    host_name = models.CharField(max_length=255, blank=True)  # who they're visiting
    badge_no = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    signed_in_at = models.DateTimeField(null=True, blank=True)
    signed_out_at = models.DateTimeField(null=True, blank=True)
    # Working-with-children / induction acknowledgement (child-safety).
    wwc_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_visitors"
        ordering = ["-created_at"]

    @property
    def on_site(self) -> bool:
        return self.signed_in_at is not None and self.signed_out_at is None

    def __str__(self):
        return f"{self.full_name} ({'on-site' if self.on_site else 'off-site'})"
