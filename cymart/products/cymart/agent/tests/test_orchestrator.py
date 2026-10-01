import uuid

import pytest

from products.cymart.agent.models import AgentMessage
from products.cymart.agent.orchestrator import AgentSession, MAX_TOOL_ROUNDS
from products.cymart.agent.providers.base import CompletionProvider, CompletionResult, ToolCall


class _ScriptedProvider(CompletionProvider):
    """Replays a fixed sequence of results — one per call to .complete()."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = []

    def complete(self, system_prompt, messages, tools):
        self.calls.append({"system_prompt": system_prompt, "messages": list(messages), "tools": tools})
        return self._results.pop(0)


class _AlwaysLoopingProvider(CompletionProvider):
    """A misbehaving/adversarial model that always asks for a tool call —
    proves the round limit stops it instead of looping forever."""

    def complete(self, system_prompt, messages, tools):
        return CompletionResult(
            tool_calls=[ToolCall(name="view_cart", arguments={}, id=str(uuid.uuid4()))],
            stop_reason="tool_use",
        )


class _RogueToolProvider(CompletionProvider):
    """Tries to call a tool that was never in the allowlist it was given —
    proves the gate refuses it regardless of the model's request."""

    def __init__(self):
        self._done = False

    def complete(self, system_prompt, messages, tools):
        if not self._done:
            self._done = True
            return CompletionResult(
                tool_calls=[ToolCall(name="web_search", arguments={"query": "anything"}, id="1")],
                stop_reason="tool_use",
            )
        return CompletionResult(text="Done.", stop_reason="end")


@pytest.mark.django_db
class TestAgentSession:
    def test_text_only_reply_is_logged(self):
        provider = _ScriptedProvider([CompletionResult(text="Hi there!", stop_reason="end")])
        customer_id = uuid.uuid4()
        result = AgentSession(provider=provider).handle(customer_id, "hello")
        assert result["reply"] == "Hi there!"
        assert result["tool_calls"] == []
        roles = list(AgentMessage.objects.filter(customer_id=customer_id).values_list("role", flat=True))
        assert roles == ["user", "assistant"]

    def test_tool_use_round_trip(self):
        provider = _ScriptedProvider(
            [
                CompletionResult(
                    tool_calls=[ToolCall(name="view_cart", arguments={}, id="c1")],
                    stop_reason="tool_use",
                ),
                CompletionResult(text="Your cart is empty.", stop_reason="end"),
            ]
        )
        result = AgentSession(provider=provider).handle(uuid.uuid4(), "what's in my cart?")
        assert result["reply"] == "Your cart is empty."
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "view_cart"
        assert result["tool_calls"][0]["output"]["items"] == []

    def test_tool_result_is_fed_back_into_the_next_call(self):
        provider = _ScriptedProvider(
            [
                CompletionResult(
                    tool_calls=[ToolCall(name="view_cart", arguments={}, id="c1")],
                    stop_reason="tool_use",
                ),
                CompletionResult(text="ok", stop_reason="end"),
            ]
        )
        AgentSession(provider=provider).handle(uuid.uuid4(), "cart?")
        second_call_messages = provider.calls[1]["messages"]
        assert any(m["role"] == "tool" for m in second_call_messages)

    def test_history_carries_across_calls(self):
        customer_id = uuid.uuid4()
        provider = _ScriptedProvider(
            [
                CompletionResult(text="first reply", stop_reason="end"),
                CompletionResult(text="second reply", stop_reason="end"),
            ]
        )
        session = AgentSession(provider=provider)
        session.handle(customer_id, "first message")
        session.handle(customer_id, "second message")
        second_call_messages = provider.calls[1]["messages"]
        contents = [m["content"] for m in second_call_messages]
        assert "first message" in contents
        assert "first reply" in contents

    def test_round_limit_stops_an_infinitely_looping_model(self):
        result = AgentSession(provider=_AlwaysLoopingProvider()).handle(uuid.uuid4(), "loop forever")
        assert result["reply"] == "Let me get someone to help with that."
        assert len(result["tool_calls"]) == MAX_TOOL_ROUNDS

    def test_rogue_tool_request_is_refused_not_executed(self):
        result = AgentSession(provider=_RogueToolProvider()).handle(uuid.uuid4(), "search the web for me")
        assert result["reply"] == "Done."
        assert result["tool_calls"][0]["name"] == "web_search"
        assert "error" in result["tool_calls"][0]["output"]
