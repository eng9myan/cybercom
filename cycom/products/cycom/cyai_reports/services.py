import json

from django.core.exceptions import ValidationError
from django.utils import timezone

from products.cycom.cyai_reports.models import (
    ReportBuilderSession,
    ReportDefinition,
    ReportRevision,
)
from products.cycom.cyai_reports.query_engine import execute_spec, validate_spec
from products.cycom.cyai_reports.registry import REPORTABLE_MODELS

SYSTEM_PROMPT = """You are the CyAI Advanced Report Builder. You help a user design a
business report by gathering requirements, then propose a report as a JSON query_spec.

Reportable models and their fields:
{registry_summary}

Respond with ONLY a JSON object, no prose outside it, in exactly this shape:
{{"type": "question", "content": "<a clarifying question>"}}
or, once you have enough information:
{{"type": "draft", "content": "<a plain-language summary of the report you're proposing>",
  "title": "<short report title>",
  "query_spec": {{"model": "<key>", "filters": {{}}, "aggregate": null, "aggregate_field": null,
                   "group_by": null, "fields": [], "limit": 100}}}}

Only use models/fields from the list above — never invent a field or model that isn't listed.
"""


def _registry_summary() -> str:
    lines = []
    for key, reg in REPORTABLE_MODELS.items():
        lines.append(
            f"- {key}: fields={sorted(reg['fields'])}, filterable={sorted(reg['filter_fields'])}, "
            f"aggregatable={sorted(reg['aggregate_fields'])}"
        )
    return "\n".join(lines)


class ReportBuilderAgent:
    @staticmethod
    def start_session(tenant_id, started_by: str = "") -> ReportBuilderSession:
        return ReportBuilderSession.objects.create(
            tenant_id=tenant_id, started_by=started_by, status="gathering"
        )

    @staticmethod
    def send_message(session: ReportBuilderSession, content: str) -> dict:
        from platform.cyai.models import ModelConfig
        from platform.cyai.services import ModelGateway

        messages = list(session.messages)
        messages.append({"role": "user", "content": content, "created_at": timezone.now().isoformat()})

        config = ModelConfig.objects.filter(provider="anthropic", active=True).first()
        if not config:
            session.messages = messages
            session.save(update_fields=["messages"])
            raise ValidationError(
                "No active Anthropic ModelConfig found. Create one via /api/v1/ai/configs/ first."
            )

        history_text = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        prompt = SYSTEM_PROMPT.format(registry_summary=_registry_summary()) + "\n\nConversation:\n" + history_text

        result = ModelGateway.generate_completion(
            tenant_id=str(session.tenant_id), config=config, prompt=prompt
        )

        if result["status"] != "passed" or not result.get("text"):
            messages.append({"role": "system_error", "content": result.get("text") or "LLM call failed", "created_at": timezone.now().isoformat()})
            session.messages = messages
            session.save(update_fields=["messages"])
            raise ValidationError(f"Report builder LLM call failed: {result}")

        try:
            parsed = json.loads(result["text"])
        except json.JSONDecodeError as exc:
            raise ValidationError(f"LLM response was not valid JSON: {exc}")

        messages.append({"role": "assistant", "content": parsed.get("content", ""), "created_at": timezone.now().isoformat()})
        session.messages = messages

        if parsed.get("type") == "draft" and parsed.get("query_spec"):
            validate_spec(parsed["query_spec"])  # raises if the LLM proposed something off-registry
            session.draft_spec = parsed["query_spec"]
            session.draft_title = parsed.get("title", "")
            session.status = "drafting"

        session.save(update_fields=["messages", "draft_spec", "draft_title", "status"])
        return parsed

    @staticmethod
    def preview(session: ReportBuilderSession) -> dict:
        """Safe, non-destructive — runs the draft spec but saves nothing."""
        if not session.draft_spec:
            raise ValidationError("No draft report to preview yet.")
        return execute_spec(session.draft_spec, session.tenant_id)

    @staticmethod
    def confirm(session: ReportBuilderSession) -> ReportDefinition:
        """The explicit-confirmation gate: nothing is saved until this is called."""
        if session.status != "drafting" or not session.draft_spec:
            raise ValidationError("Session has no confirmed-ready draft.")

        report = ReportDefinition.objects.create(
            tenant_id=session.tenant_id,
            name=session.draft_title or "Untitled Report",
            query_spec=session.draft_spec,
            owner=session.started_by,
            current_version=1,
        )
        ReportRevision.objects.create(
            tenant_id=session.tenant_id,
            report=report,
            version=1,
            query_spec=session.draft_spec,
            change_summary="Initial version, confirmed from builder session.",
            created_by=session.started_by,
        )
        session.status = "confirmed"
        session.saved_report = report
        session.save(update_fields=["status", "saved_report"])
        return report
