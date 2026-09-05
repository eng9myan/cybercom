"""
Simulation bookkeeping (see cyshop apps.simulations for the shared rationale).

The engine writes ordinary clinical records — encounters, ED visits,
admissions, bed assignments, orders/results — into the real cymed tables so a
demo tenant behaves like a working hospital + clinic network. `SimulationRun`
is the one row the simulation keeps for itself: the manifest of a run (seed,
parameters, KPI rollup, record counts) so it can be wiped and replayed.
"""
from django.db import models

from platform.common.models import BaseModel


class SimulationRun(BaseModel):
    STATUS = [
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    scenario = models.CharField(max_length=64)
    seed = models.BigIntegerField(default=0)
    start_date = models.DateField()
    days = models.PositiveIntegerField(default=7)
    status = models.CharField(max_length=16, choices=STATUS, default="RUNNING")

    parameters = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    record_counts = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_simulation_runs"
        ordering = ["-created_at"]

    @property
    def tag(self) -> str:
        return f"SIM:{self.scenario}:{str(self.id)[:8]}"

    def __str__(self) -> str:
        return f"{self.scenario} @ {self.start_date} (+{self.days}d) [{self.status}]"
