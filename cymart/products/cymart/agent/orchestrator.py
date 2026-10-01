"""AgentSession — the loop: call the completion provider, execute any
tool calls through the gate, feed results back, repeat until the model
returns plain text (or the round limit trips).

The provider is swappable (CYMART_AGENT_PROVIDER, sandbox by default);
the tool list handed to it is always exactly tools.ALLOWED_TOOLS — the
model is never given a web-search, email, or code-exec tool, so "asking
outside the system" has nowhere to go even if the prompt is ignored.
Conversation history is rebuilt from AgentMessage rows, not a
client-supplied array, so a caller can't inject fake assistant/tool
turns into their own context.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.utils.module_loading import import_string

from .models import AgentMessage, AgentMessageRole
from .tools import ALLOWED_TOOLS, OutOfScopeToolError, execute_tool

SYSTEM_PROMPT = (
    "You are the CyMart ordering assistant. You help the caller order "
    "food and groceries from vendors connected to CyMart, check their "
    "diet plan, manage their cart, and check the status of their own "
    "orders — using only the tools you are given. You have no general "
    "knowledge tools, no web access, and no way to act outside CyMart. "
    "If asked about anything outside food ordering, groceries, or the "
    "caller's own CyMart account, say plainly that you can only help "
    "with CyMart ordering and steer the conversation back to that."
)

MAX_TOOL_ROUNDS = 4
HISTORY_TURNS = 10
FALLBACK_REPLY = "Let me get someone to help with that."


def _tool_schemas() -> list[dict]:
    return [
        {"name": t.name, "description": t.description, "parameters": t.parameters}
        for t in ALLOWED_TOOLS.values()
    ]


class AgentSession:
    def __init__(self, provider=None):
        if provider is not None:
            self._provider = provider
        else:
            provider_path = getattr(
                settings,
                "CYMART_AGENT_PROVIDER",
                "products.cymart.agent.providers.sandbox.SandboxCompletionProvider",
            )
            self._provider = import_string(provider_path)()

    def _load_history(self, customer_id: uuid.UUID) -> list[dict]:
        rows = AgentMessage.objects.filter(customer_id=customer_id).order_by("-created_at")[
            :HISTORY_TURNS
        ]
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]

    def handle(self, customer_id: uuid.UUID, user_text: str) -> dict:
        messages = self._load_history(customer_id)
        messages.append({"role": "user", "content": user_text})
        AgentMessage.objects.create(
            customer_id=customer_id, role=AgentMessageRole.USER, content=user_text
        )

        tool_log: list[dict] = []
        for _ in range(MAX_TOOL_ROUNDS):
            result = self._provider.complete(SYSTEM_PROMPT, messages, _tool_schemas())

            if result.stop_reason != "tool_use" or not result.tool_calls:
                AgentMessage.objects.create(
                    customer_id=customer_id, role=AgentMessageRole.ASSISTANT, content=result.text
                )
                return {"reply": result.text, "tool_calls": tool_log}

            messages.append(
                {
                    "role": "assistant",
                    "content": result.text,
                    "tool_calls": [
                        {"id": c.id, "name": c.name, "arguments": c.arguments}
                        for c in result.tool_calls
                    ],
                }
            )
            for call in result.tool_calls:
                try:
                    output = execute_tool(call.name, customer_id, **call.arguments)
                except OutOfScopeToolError as exc:
                    # The gate refused it — the model asked for something
                    # off the allowlist. Report the refusal back as the
                    # tool's result instead of executing anything.
                    output = {"error": str(exc)}
                tool_log.append({"name": call.name, "arguments": call.arguments, "output": output})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": output,
                    }
                )

        AgentMessage.objects.create(
            customer_id=customer_id, role=AgentMessageRole.ASSISTANT, content=FALLBACK_REPLY
        )
        return {"reply": FALLBACK_REPLY, "tool_calls": tool_log}
