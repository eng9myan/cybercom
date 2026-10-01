"""Real Claude adapter — Messages API with function-calling, restricted
to exactly tools.ALLOWED_TOOLS. Requires ANTHROPIC_API_KEY; the
``anthropic`` package is imported lazily so its absence never breaks the
sandbox default. Enable via:

    CYMART_AGENT_PROVIDER = "products.cymart.agent.providers.claude.ClaudeCompletionProvider"
    ANTHROPIC_API_KEY = "..."  # or the ANTHROPIC_API_KEY env var

No credentials exist in this environment — this class is unexercised by
the test suite (see providers/sandbox.py for what tests run against),
same posture as payments.providers for a real gateway.
"""

import os

from django.conf import settings

from .base import CompletionProvider, CompletionResult, ToolCall

DEFAULT_MODEL = "claude-sonnet-5"


class ClaudeCompletionProvider(CompletionProvider):
    def __init__(self, model: str | None = None):
        self._model = model or getattr(settings, "CYMART_AGENT_MODEL", DEFAULT_MODEL)

    def _client(self):
        import anthropic  # lazy — only needed when this provider is selected

        api_key = getattr(settings, "ANTHROPIC_API_KEY", None) or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
        return anthropic.Anthropic(api_key=api_key)

    def complete(self, system_prompt: str, messages: list[dict], tools: list[dict]) -> CompletionResult:
        client = self._client()
        claude_tools = [
            {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
            for t in tools
        ]

        response = client.messages.create(
            model=self._model,
            system=system_prompt,
            tools=claude_tools,
            messages=self._to_claude_messages(messages),
            max_tokens=1024,
        )

        text = "".join(block.text for block in response.content if block.type == "text")
        tool_calls = [
            ToolCall(name=block.name, arguments=block.input, id=block.id)
            for block in response.content
            if block.type == "tool_use"
        ]
        stop_reason = "tool_use" if tool_calls else "end"
        return CompletionResult(text=text, tool_calls=tool_calls, stop_reason=stop_reason)

    def _to_claude_messages(self, messages: list[dict]) -> list[dict]:
        """Collapses the orchestrator's simple {user, assistant, tool}
        protocol into Claude's message format — a tool result becomes a
        tool_result content block on a user-role turn."""
        out = []
        for m in messages:
            role = m.get("role")
            if role == "user":
                out.append({"role": "user", "content": m["content"]})
            elif role == "assistant":
                out.append({"role": "assistant", "content": m.get("content") or ""})
            elif role == "tool":
                out.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": m.get("tool_call_id", ""),
                                "content": str(m.get("content")),
                            }
                        ],
                    }
                )
        return out
