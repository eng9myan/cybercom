from django.db import models

from platform.common.models import BaseModel


class AutomationRule(BaseModel):
    """
    A no-code "when X happens, if Y, then do Z" rule.

    `trigger_source`, every condition's `field`, and every action's target
    are resolved through automation.registry -- a rule can never name a
    model or attribute directly (see registry.py).

    conditions: [{"field": "status", "operator": "eq", "value": "confirmed"}]
    actions:    [{"type": "set_field", "field": "priority", "value": "high"}]
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    trigger_source = models.CharField(max_length=50)
    trigger_event = models.CharField(max_length=30, default="created_or_updated")

    conditions = models.JSONField(default=list, blank=True)
    # All conditions must hold (AND). An OR rule is expressed as two rules --
    # deliberately no nested boolean tree in v1; it doubles the builder UI's
    # complexity for a case that two rules already cover.
    actions = models.JSONField(default=list, blank=True)

    run_count = models.PositiveIntegerField(default=0)
    last_run_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_automation_rules"
        ordering = ["name"]
        indexes = [models.Index(fields=["tenant_id", "trigger_source", "is_active"])]

    def __str__(self):
        return self.name


class AutomationRun(BaseModel):
    """One execution of a rule against one record -- the audit trail that
    makes an automation debuggable instead of a black box."""

    STATUS = [
        ("matched", "Matched, actions ran"),
        ("skipped", "Conditions not met"),
        ("failed", "Action error"),
    ]

    rule = models.ForeignKey(AutomationRule, on_delete=models.CASCADE, related_name="runs")
    record_id = models.CharField(max_length=64, blank=True)
    event = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS)
    detail = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_automation_runs"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant_id", "rule", "-created_at"])]

    def __str__(self):
        return f"{self.rule_id} {self.status}"
