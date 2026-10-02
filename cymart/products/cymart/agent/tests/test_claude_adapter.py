"""Offline tests for the real-Claude adapter: message conversion and response parsing.
The network call itself is never made here (and has not been run against the live API)."""

import json
from types import SimpleNamespace

import pytest

from products.cymart.agent.providers.claude import ClaudeCompletionProvider, to_claude_messages


def _transcript():
    return [
        {"role": "user", "content": "add milk and bread"},
        {
            "role": "assistant",
            "content": "On it.",
            "tool_calls": [
                {"id": "t1", "name": "search_catalog", "arguments": {"query": "milk"}},
                {"id": "t2", "name": "search_catalog", "arguments": {"query": "bread"}},
            ],
        },
        {"role": "tool", "tool_call_id": "t1", "name": "search_catalog", "content": {"results": [{"name": "Milk 1L"}]}},
        {"role": "tool", "tool_call_id": "t2", "name": "search_catalog", "content": {"results": [{"name": "Bread"}]}},
    ]


class TestToClaudeMessages:
    def test_assistant_tool_calls_become_tool_use_blocks(self):
        out = to_claude_messages(_transcript())
        assistant = out[1]
        assert assistant["role"] == "assistant"
        kinds = [b["type"] for b in assistant["content"]]
        assert kinds == ["text", "tool_use", "tool_use"]
        assert assistant["content"][1] == {
            "type": "tool_use", "id": "t1", "name": "search_catalog", "input": {"query": "milk"}
        }

    def test_all_results_for_one_turn_share_one_user_message(self):
        out = to_claude_messages(_transcript())
        assert [m["role"] for m in out] == ["user", "assistant", "user"]
        results = out[2]["content"]
        assert [r["tool_use_id"] for r in results] == ["t1", "t2"]
        assert all(r["type"] == "tool_result" for r in results)

    def test_every_tool_result_follows_its_tool_use(self):
        out = to_claude_messages(_transcript())
        used = {b["id"] for m in out if m["role"] == "assistant" for b in m["content"] if b["type"] == "tool_use"}
        answered = {b["tool_use_id"] for m in out if m["role"] == "user" and isinstance(m["content"], list) for b in m["content"]}
        assert answered <= used

    def test_tool_output_is_sent_as_json_not_python_repr(self):
        out = to_claude_messages(_transcript())
        payload = json.loads(out[2]["content"][0]["content"])
        assert payload == {"results": [{"name": "Milk 1L"}]}

    def test_arabic_survives_conversion(self):
        msgs = [
            {"role": "user", "content": "أريد حليب"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "a", "name": "search_catalog", "arguments": {"query": "حليب"}}]},
            {"role": "tool", "tool_call_id": "a", "name": "search_catalog", "content": {"results": [{"name": "حليب كامل"}]}},
        ]
        out = to_claude_messages(msgs)
        assert out[1]["content"] == [{"type": "tool_use", "id": "a", "name": "search_catalog", "input": {"query": "حليب"}}]
        assert "حليب كامل" in out[2]["content"][0]["content"]  # not escaped to \u sequences

    def test_empty_assistant_turn_is_skipped(self):
        out = to_claude_messages([{"role": "user", "content": "hi"}, {"role": "assistant", "content": ""}])
        assert [m["role"] for m in out] == ["user"]

    def test_plain_text_history_round_trips(self):
        out = to_claude_messages([
            {"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}, {"role": "user", "content": "milk"},
        ])
        assert out[1] == {"role": "assistant", "content": [{"type": "text", "text": "hello"}]}


class TestComplete:
    def _provider_with(self, content, captured):
        class FakeMessages:
            def create(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(content=content)

        provider = ClaudeCompletionProvider(model="test-model")
        provider._client = lambda: SimpleNamespace(messages=FakeMessages())
        return provider

    def test_tool_use_response_is_parsed(self):
        captured = {}
        content = [
            SimpleNamespace(type="text", text="Searching."),
            SimpleNamespace(type="tool_use", id="tu_1", name="search_catalog", input={"query": "milk"}),
        ]
        tools = [{"name": "search_catalog", "description": "d", "parameters": {"type": "object", "properties": {}}}]
        result = self._provider_with(content, captured).complete("sys", _transcript(), tools)
        assert result.stop_reason == "tool_use"
        assert result.text == "Searching."
        assert (result.tool_calls[0].name, result.tool_calls[0].arguments, result.tool_calls[0].id) == (
            "search_catalog", {"query": "milk"}, "tu_1")
        assert captured["model"] == "test-model" and captured["system"] == "sys"
        assert captured["tools"][0]["input_schema"] == {"type": "object", "properties": {}}
        assert [m["role"] for m in captured["messages"]] == ["user", "assistant", "user"]

    def test_text_only_response_ends_the_turn(self):
        result = self._provider_with([SimpleNamespace(type="text", text="Done.")], {}).complete("s", [{"role": "user", "content": "x"}], [])
        assert result.stop_reason == "end" and result.tool_calls == [] and result.text == "Done."

    def test_missing_api_key_raises(self, monkeypatch, settings):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        settings.ANTHROPIC_API_KEY = None
        pytest.importorskip("anthropic")
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            ClaudeCompletionProvider()._client()
