from django.db import models

from platform.common.models import BaseModel


class Campus(BaseModel):
    """
    A single campus within a school group. The tenant is the GROUP; a group runs
    many campuses. Core records (students, staff, classes, bills) carry a campus
    FK so central office gets both per-campus and consolidated (group) views.
    """

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, blank=True)  # short code, e.g. "JNR", "SNR-VIC"
    address = models.CharField(max_length=500, blank=True)
    suburb = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=20, blank=True)  # NSW / VIC / ...
    postcode = models.CharField(max_length=10, blank=True)
    principal_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_campuses"
        ordering = ["name"]
        constraints = [
            # Codes are optional; only enforce uniqueness on non-blank codes so
            # multiple campuses may be created before codes are assigned.
            models.UniqueConstraint(
                fields=["tenant_id", "code"], name="uniq_campus_code_per_group",
                condition=~models.Q(code=""),
            )
        ]

    def __str__(self):
        return self.name
