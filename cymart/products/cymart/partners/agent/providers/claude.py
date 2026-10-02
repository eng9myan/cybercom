"""Claude adapter (Anthropic Messages API, tool use). Select it with

    DIET_SHIELD_AGENT_PROVIDER=partners.agent.providers.claude.ClaudeCompletionProvider
    ANTHROPIC_API_KEY=...            (environment only; never stored or logged)
    DIET_SHIELD_AGENT_MODEL=...      (optional; default below)

STATUS: not exercised against the live API — no valid key was available when this
was built. The message conversion is unit-tested offline (tests/test_agent.py); the
network call itself is not. Run one real turn before relying on it.

The ``anthropic`` package is imported lazily so its absence never affects the sandbox.
"""

import json
import os

from .base import Completion, CompletionProvider, ToolCall

DEFAULT_MODEL = "claude-sonnet-5-5"


def to_claude_messages(messages: list[dict]) -> list[dict]:
    """Transcript protocol -> Anthropic format. An assistant turn that made a tool
    call becomes text + tool_use blocks, and the tool's result becomes a tool_result
    block on the next user turn; Anthropic requires every tool_result to follow its tool_use."""
    out: list[dict] = []
    for m in messages:
        role = m.get("role")
        if role == "user":
            out.append({"role": "user", "content": m["content"]})
        elif role == "assistant":
            blocks = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for c in m.get("tool_calls") or []:
                blocks.append({"type": "tool_use", "id": c["id"], "name": c["name"], "input": c.get("arguments") or {}})
            if blocks:
                out.append({"role": "assistant", "content": blocks})
        elif role == "tool":
            content = m.get("content")
            block = {
                "type": "tool_result", "tool_use_id": m["tool_call_id"],
                "content": content if isinstance(content, str) else json.dumps(content, ensure_ascii=False),
            }
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
    return out


class ClaudeCompletionProvider(CompletionProvider):
    def __init__(self, model: str | None = None):
        self._model = model or os.environ.get("DIET_SHIELD_AGENT_MODEL", DEFAULT_MODEL)

    def _client(self):
        import anthropic

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        return anthropic.Anthropic(api_key=key)

    def complete(self, system, messages, tools, language="en") -> Completion:
        response = self._client().messages.create(
            model=self._model,
            system=system,
            tools=[{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]} for t in tools],
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=to_claude_messages(messages),
            max_tokens=800,
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        calls = [ToolCall(name=b.name, arguments=dict(b.input), id=b.id) for b in response.content if b.type == "tool_use"]
        return Completion(text=text, tool_calls=calls)
