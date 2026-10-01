"""Deterministic offline provider — routes on simple keyword matching so
the tool gate and the orchestrator's tool-use loop are fully testable
without any LLM API key. This is the default (settings.CYMART_AGENT_
PROVIDER), same role sandbox.py plays for payments. Swap in
providers.claude.ClaudeCompletionProvider for a real model.
"""

import uuid

from .base import CompletionProvider, CompletionResult, ToolCall

OFF_TOPIC_REPLY = (
    "I can only help with CyMart ordering — food and groceries from "
    "vendors connected to CyMart, your diet plan, your cart, and your "
    "orders. What would you like to order or check?"
)

DEFAULT_REPLY = (
    "I can help you order food or groceries, check your diet plan, or "
    "manage your cart. What would you like to do?"
)


class SandboxCompletionProvider(CompletionProvider):
    def complete(self, system_prompt: str, messages: list[dict], tools: list[dict]) -> CompletionResult:
        # Re-invoked after a tool result — summarize it and stop.
        if messages and messages[-1].get("role") == "tool":
            return CompletionResult(text=self._summarize(messages[-1]), stop_reason="end")

        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        text = (last_user or "").lower()

        if "cart" in text:
            return CompletionResult(
                tool_calls=[ToolCall(name="view_cart", arguments={}, id=str(uuid.uuid4()))],
                stop_reason="tool_use",
            )
        if any(w in text for w in ("plan", "diet", "calorie", "budget")):
            return CompletionResult(
                tool_calls=[ToolCall(name="diet_plan_status", arguments={}, id=str(uuid.uuid4()))],
                stop_reason="tool_use",
            )
        if any(w in text for w in ("low on", "running out", "replenish", "refill")):
            return CompletionResult(
                tool_calls=[ToolCall(name="replenish_basket", arguments={}, id=str(uuid.uuid4()))],
                stop_reason="tool_use",
            )
        if any(w in text for w in ("weather", "news", "stock price", "joke", "who is")):
            return CompletionResult(text=OFF_TOPIC_REPLY, stop_reason="end")

        return CompletionResult(text=DEFAULT_REPLY, stop_reason="end")

    def _summarize(self, tool_message: dict) -> str:
        return f"Here's what I found: {tool_message.get('content')}"
