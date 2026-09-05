"""
Simulation bookkeeping.

The simulation engine writes ordinary business records (POS orders, stock
movements, purchase orders, ...) into the real cyshop tables so the demo
tenant looks and behaves like a live operation. `SimulationRun` is the one
extra row it keeps for itself: a manifest of what a given run produced, its
seed and parameters (so it is reproducible), and the KPI rollup it computed.

Every business row a run creates is tagged with the run tag
(`SimulationRun.tag`) in its `reference` / `notes` field, so a run can be
wiped and replayed deterministically.
"""
from django.db import models

from apps.tenants.models import BaseEntity


class SimulationRun(BaseEntity):
    STATUS = [
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    scenario = models.CharField(max_length=64)
    seed = models.BigIntegerField(default=0)
    start_date = models.DateField(help_text="First simulated day.")
    days = models.PositiveIntegerField(default=7)
    status = models.CharField(max_length=16, choices=STATUS, default="RUNNING")

    parameters = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)

    record_counts = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def tag(self) -> str:
        return f"SIM:{self.scenario}:{str(self.id)[:8]}"

    def __str__(self) -> str:
        return f"{self.scenario} @ {self.start_date} (+{self.days}d) [{self.status}]"
