"""Completion provider interface. The orchestrator, the tool registry and the plan
gate never depend on which model is behind it: swap the provider, nothing else changes."""

import abc
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict
    id: str = ""


@dataclass
class Completion:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class CompletionProvider(abc.ABC):
    @abc.abstractmethod
    def complete(self, system: str, messages: list[dict], tools: list[dict], language: str = "en") -> Completion:
        """messages use the transcript protocol:
            {"role": "user", "content": str}
            {"role": "assistant", "content": str, "tool_calls": [{"id", "name", "arguments"}]}
            {"role": "tool", "tool_call_id", "name", "content": json}
        ``tools`` is the closed list from tools.specs_for(); the model is never shown anything else."""
