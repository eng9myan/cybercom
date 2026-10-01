"""Completion provider abstraction — mirrors payments.providers.base. A
real LLM adapter (Claude, etc.) implements this same interface; no API
key exists in this environment, so only the interface plus a
deterministic sandbox implementation are wired up by default. Swapping
in a real provider means implementing this interface and pointing
settings.CYMART_AGENT_PROVIDER at it — not changing AgentSession or the
tool gate.
"""

import abc
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict
    id: str = ""


@dataclass
class CompletionResult:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end"  # "end" | "tool_use"


class CompletionProvider(abc.ABC):
    @abc.abstractmethod
    def complete(self, system_prompt: str, messages: list[dict], tools: list[dict]) -> CompletionResult:
        """messages: [{"role": "user"|"assistant"|"tool", ...}] in the
        orchestrator's own simple protocol (see AgentSession). tools is
        the JSON-schema list built from tools.ALLOWED_TOOLS — the model is
        never given anything outside that list."""
