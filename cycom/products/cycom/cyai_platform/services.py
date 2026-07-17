from products.cycom.cyai_platform.models import AgentDefinition, AgentEntitlement, AgentKey, AgentUsageRecord

# Deterministic, zero-LLM-cost keyword routing — matches the spec's own
# routing examples. Checked in priority order: BUILDER_AI signals (build a
# NEW capability) outrank REPORT_STUDIO signals (persist a reusable report),
# which outrank the ASK_CYCOM default (everything else — search/answer/
# navigate). A question can plausibly contain multiple signal words ("build
# a report" is ambiguous in English); priority order resolves it the way the
# spec's own examples imply, rather than trying to be clever about it.
_BUILDER_AI_SIGNALS = [
    "build", "workflow", "module", "integration", "implement", "automation",
    "approval flow", "webhook", "onboarding", "extension", "connector",
]
_REPORT_STUDIO_SIGNALS = [
    "report", "dashboard", "comparison", "compare", "reusable", "permanent",
    "recurring", "pivot",
]


def route_question(question: str) -> dict:
    """Returns {agent_key, confidence, requires_confirmation}. Confidence is
    a simple signal-match indicator, not a calibrated probability — good
    enough to decide whether to ask the user for confirmation before
    transferring to a separately-billed agent, which is all this needs to do."""
    text = question.lower()

    for kw in _BUILDER_AI_SIGNALS:
        if kw in text:
            return {"agent_key": AgentKey.BUILDER_AI, "confidence": 0.8, "requires_confirmation": True}
    for kw in _REPORT_STUDIO_SIGNALS:
        if kw in text:
            return {"agent_key": AgentKey.REPORT_STUDIO, "confidence": 0.7, "requires_confirmation": True}
    return {"agent_key": AgentKey.ASK_CYCOM, "confidence": 0.5, "requires_confirmation": False}


def has_active_entitlement(tenant_id, agent_key: str) -> bool:
    return AgentEntitlement.objects.filter(
        tenant_id=tenant_id, agent__agent_key=agent_key, is_active=True
    ).exists()


def grant_entitlement(tenant_id, agent_key: str, plan_code: str = "", granted_by: str = "") -> AgentEntitlement:
    agent = AgentDefinition.objects.get(agent_key=agent_key)
    entitlement, _ = AgentEntitlement.objects.update_or_create(
        tenant_id=tenant_id,
        agent=agent,
        defaults={"is_active": True, "plan_code": plan_code, "granted_by": granted_by},
    )
    return entitlement


def revoke_entitlement(tenant_id, agent_key: str) -> None:
    AgentEntitlement.objects.filter(tenant_id=tenant_id, agent__agent_key=agent_key).update(is_active=False)


def record_usage(tenant_id, agent_key: str, user_id: str, request_type: str, routed_confidence=None):
    agent = AgentDefinition.objects.get(agent_key=agent_key)
    return AgentUsageRecord.objects.create(
        tenant_id=tenant_id,
        agent=agent,
        user_id=user_id,
        request_type=request_type,
        routed_confidence=routed_confidence,
    )
