"""
Simulation bookkeeping.

The engines write ordinary business records (logistics shipments / delivery
orders / routes, sales orders, manufacturing orders) into the real cycom tables
so a demo tenant behaves like a working operation. `SimulationRun` is the one
row a run keeps for itself. It is a plain model (not the tenant-scoped
`BaseModel`) so the management command can create it before the demo tenant's
ambient context is established.
"""
import uuid

from django.db import models
from django.utils import timezone


class SimulationRun(models.Model):
    STATUS = [("RUNNING", "Running"), ("COMPLETED", "Completed"), ("FAILED", "Failed")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    scenario = models.CharField(max_length=64)
    seed = models.BigIntegerField(default=0)
    start_date = models.DateField()
    days = models.PositiveIntegerField(default=7)
    status = models.CharField(max_length=16, choices=STATUS, default="RUNNING")

    parameters = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    record_counts = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_simulation_runs"
        ordering = ["-created_at"]

    @property
    def tag(self) -> str:
        return f"SIM:{self.scenario}:{str(self.id)[:8]}"

    def __str__(self) -> str:
        return f"{self.scenario} @ {self.start_date} (+{self.days}d) [{self.status}]"
