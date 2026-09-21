from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone

from platform.common.models import BaseModel

PRIORITY_CHOICES = [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")]
STAGE_CHOICES = [
    ("new", "New"),
    ("in_progress", "In Progress"),
    ("waiting", "Waiting"),
    ("solved", "Solved"),
    ("closed", "Closed"),
]


class SLAPolicy(BaseModel):
    """Target resolution time for tickets matching a team/priority. Blank
    team or priority means "any" — resolve_for picks the most specific
    active match."""

    name = models.CharField(max_length=255)
    team = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, blank=True)
    resolution_hours = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_helpdesk_sla_policies"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @classmethod
    def resolve_for(cls, tenant_id, team, priority):
        candidates = list(
            cls.objects.filter(tenant_id=tenant_id, is_active=True)
            .filter(Q(team=team) | Q(team=""))
            .filter(Q(priority=priority) | Q(priority=""))
        )
        if not candidates:
            return None
        candidates.sort(key=lambda p: (p.team == team, p.priority == priority), reverse=True)
        return candidates[0]


class Ticket(BaseModel):
    PRIORITY = PRIORITY_CHOICES
    STAGE = STAGE_CHOICES

    number = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255, blank=True)
    assignee = models.CharField(max_length=255, blank=True)
    team = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY, default="normal")
    stage = models.CharField(max_length=20, choices=STAGE, default="new")
    description = models.TextField(blank=True)

    sla_policy = models.ForeignKey(
        SLAPolicy, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets"
    )
    sla_deadline = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_helpdesk_tickets"
        unique_together = [("tenant_id", "number")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} — {self.subject}"

    @property
    def is_breached(self):
        if not self.sla_deadline:
            return False
        end = self.resolved_at or timezone.now()
        return end > self.sla_deadline

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if is_new and not self.sla_policy_id and self.tenant_id:
            policy = SLAPolicy.resolve_for(self.tenant_id, self.team, self.priority)
            if policy:
                self.sla_policy = policy
                self.sla_deadline = timezone.now() + timedelta(hours=policy.resolution_hours)
        if self.stage in ("solved", "closed") and self.resolved_at is None:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)
