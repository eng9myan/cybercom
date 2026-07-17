from django.db import models

from platform.common.models import BaseModel, PlatformModel


class QueryPlan(PlatformModel):
    """
    Metadata/audit record for a validated, code-defined query plan (the
    actual query logic lives in cyai_memory/plans.py as a reviewed Python
    function — this table is for discoverability and usage tracking, not
    dynamic execution. Only plans with a matching entry in PLAN_REGISTRY
    are ever actually runnable; this table can't execute arbitrary code.
    Not tenant-scoped — the plan catalog is the same code for every tenant.
    """

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    example_questions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_cyai_query_plans"
        ordering = ["name"]

    def __str__(self):
        return self.code


class MemoryQueryLog(BaseModel):
    """Audit trail for every question the Local Memory Agent handled."""

    question = models.TextField()
    matched_plan_code = models.CharField(max_length=100, blank=True)
    params = models.JSONField(default=dict, blank=True)
    answer_text = models.TextField(blank=True)
    used_llm_fallback = models.BooleanField(default=False)
    asked_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_cyai_memory_query_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.matched_plan_code or 'unmatched'}: {self.question[:50]}"
