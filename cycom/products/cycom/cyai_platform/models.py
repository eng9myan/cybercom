from django.db import models

from platform.common.models import BaseModel, PlatformModel

# Foundation layer for the CyCom three-agent AI platform: a platform-wide
# catalog of the 3 agents (same 3 for every tenant), per-tenant entitlements
# (schema only — no live billing/payment integration here), and per-agent
# usage records for future metering. Deliberately NOT wired yet as an
# enforcement gate on the existing cyai_memory/cyai_reports/cyai_moduledev
# endpoints — those stay open to any authenticated tenant user until a
# separate, explicit pass flips that switch (a real behavior change for
# already-verified features, not something to fold silently into "foundation").


class AgentKey(models.TextChoices):
    ASK_CYCOM = "ask_cycom", "Ask CyCom"
    REPORT_STUDIO = "report_studio", "CyCom Report Studio AI"
    BUILDER_AI = "builder_ai", "CyCom Builder AI"


class AgentDefinition(PlatformModel):
    agent_key = models.CharField(max_length=30, choices=AgentKey.choices, unique=True)
    customer_facing_name = models.CharField(max_length=100)
    purpose = models.TextField()
    capabilities = models.JSONField(default=list, blank=True)
    requires_elevated_approval = models.BooleanField(default=False)
    # Informational only — not wired to any payment provider. Mirrors the
    # commercial model the user specified; changing these fields has zero
    # effect on access until a real billing integration reads them.
    suggested_pricing_note = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_cyai_agent_definitions"
        ordering = ["agent_key"]

    def __str__(self):
        return self.customer_facing_name


class AgentEntitlement(BaseModel):
    """A tenant's access grant to one agent. Schema-only for now — no
    payment gateway, no numeric quota enforcement. Existence + is_active
    is the entire check."""

    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name="entitlements")
    plan_code = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    monthly_allowance = models.PositiveIntegerField(null=True, blank=True)
    granted_by = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_cyai_agent_entitlements"
        unique_together = [("tenant_id", "agent")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tenant_id} -> {self.agent.agent_key} ({'active' if self.is_active else 'inactive'})"


class AgentUsageRecord(BaseModel):
    """One row per agent invocation — separate from cyai_analytics'
    aggregation over the other apps' own logs, this is agent-level metering
    intended for future entitlement/allowance enforcement."""

    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name="usage_records")
    user_id = models.CharField(max_length=255, blank=True)
    request_type = models.CharField(max_length=50)
    routed_confidence = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "cycom_cyai_agent_usage_records"
        ordering = ["-created_at"]
