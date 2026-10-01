import uuid

import pytest

from products.cymart.agent.orchestrator import AgentSession
from products.cymart.agent.providers.sandbox import (
    DEFAULT_REPLY,
    OFF_TOPIC_REPLY,
    SandboxCompletionProvider,
)


@pytest.mark.django_db
class TestSandboxProviderEndToEnd:
    def test_cart_question_routes_to_view_cart_tool(self):
        result = AgentSession(provider=SandboxCompletionProvider()).handle(
            uuid.uuid4(), "what's in my cart?"
        )
        assert result["tool_calls"][0]["name"] == "view_cart"
        assert "cart" in result["reply"].lower() or "found" in result["reply"].lower()

    def test_diet_question_routes_to_plan_status_tool(self):
        result = AgentSession(provider=SandboxCompletionProvider()).handle(
            uuid.uuid4(), "how's my diet plan doing today?"
        )
        assert result["tool_calls"][0]["name"] == "diet_plan_status"

    def test_off_topic_request_is_declined_not_answered(self):
        result = AgentSession(provider=SandboxCompletionProvider()).handle(
            uuid.uuid4(), "what's the weather like today?"
        )
        assert result["reply"] == OFF_TOPIC_REPLY
        assert result["tool_calls"] == []

    def test_generic_greeting_offers_cymart_help_only(self):
        result = AgentSession(provider=SandboxCompletionProvider()).handle(uuid.uuid4(), "hi")
        assert result["reply"] == DEFAULT_REPLY
        assert result["tool_calls"] == []
