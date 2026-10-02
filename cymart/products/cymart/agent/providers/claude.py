"""Real Claude adapter — Messages API with function-calling, restricted
to exactly tools.ALLOWED_TOOLS. Requires ANTHROPIC_API_KEY; the
``anthropic`` package is imported lazily so its absence never breaks the
sandbox default. Enable via:

    CYMART_AGENT_PROVIDER = "products.cymart.agent.providers.claude.ClaudeCompletionProvider"
    ANTHROPIC_API_KEY = "..."  # or the ANTHROPIC_API_KEY env var

STATUS: the message conversion and response parsing are unit-tested offline
(agent/tests/test_claude_adapter.py). The network call itself has NOT been run
against the live API — no valid key was available. Run one real turn before
relying on it.
"""

import json
import os

from django.conf import settings

from .base import CompletionProvider, CompletionResult, ToolCall

DEFAULT_MODEL = "claude-sonnet-5-5"


def to_claude_messages(messages: list[dict]) -> list[dict]:
    """Collapses the orchestrator's simple {user, assistant, tool} protocol into
    Claude's message format.

    Anthropic requires every ``tool_result`` to follow the ``tool_use`` it
    answers, so an assistant turn that made tool calls must be sent as text +
    ``tool_use`` blocks (not as plain text), and ALL results for one assistant turn
    go in a single user message, one ``tool_result`` block per call. Empty text is
    rejected by the API, so empty assistant turns are skipped.
    """
    out: list[dict] = []
    for m in messages:
        role = m.get("role")
        if role == "user":
            out.append({"role": "user", "content": m["content"]})
        elif role == "assistant":
            blocks = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for call in m.get("tool_calls") or []:
                blocks.append(
                    {"type": "tool_use", "id": call["id"], "name": call["name"], "input": call.get("arguments") or {}}
                )
            if blocks:
                out.append({"role": "assistant", "content": blocks})
        elif role == "tool":
            content = m.get("content")
            block = {
                "type": "tool_result",
                "tool_use_id": m.get("tool_call_id", ""),
                "content": content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, default=str),
            }
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
    return out


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
            messages=to_claude_messages(messages),
            max_tokens=1024,
        )

        text = "".join(block.text for block in response.content if block.type == "text")
        tool_calls = [
            ToolCall(name=block.name, arguments=dict(block.input), id=block.id)
            for block in response.content
            if block.type == "tool_use"
        ]
        stop_reason = "tool_use" if tool_calls else "end"
        return CompletionResult(text=text, tool_calls=tool_calls, stop_reason=stop_reason)

    # kept for callers that used the old private name
    _to_claude_messages = staticmethod(to_claude_messages)
