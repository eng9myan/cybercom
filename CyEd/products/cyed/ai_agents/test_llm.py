from unittest.mock import patch

from products.cyed.ai_agents import llm


def test_disabled_returns_none(monkeypatch):
    monkeypatch.delenv("CYED_LLM_ENABLED", raising=False)
    assert llm.generate(question="q", context="c") is None


def test_enabled_without_key_returns_none(monkeypatch):
    monkeypatch.setenv("CYED_LLM_ENABLED", "1")
    monkeypatch.delenv("CYED_ANTHROPIC_API_KEY", raising=False)
    assert llm.generate(question="q", context="c") is None


def test_enabled_calls_anthropic_with_grounded_prompt(monkeypatch):
    monkeypatch.setenv("CYED_LLM_ENABLED", "1")
    monkeypatch.setenv("CYED_ANTHROPIC_API_KEY", "test-key")

    captured = {}

    def fake_post(payload, api_key, timeout=30):
        captured["payload"] = payload
        captured["api_key"] = api_key
        return {"content": [{"type": "text", "text": "Irrational numbers... (AC9M8N01)."}]}

    with patch.object(llm, "_post", side_effect=fake_post):
        out = llm.generate(
            question="Explain irrational numbers",
            context="[AC9M8N01] Mathematics Y8 Number: Recognise irrational numbers.",
            model_name="claude-sonnet-5",
        )

    assert out == "Irrational numbers... (AC9M8N01)."
    assert captured["api_key"] == "test-key"
    assert captured["payload"]["model"] == "claude-sonnet-5"
    # Grounding is enforced and the context is passed to the model.
    assert "ONLY" in captured["payload"]["system"]
    assert "AC9M8N01" in captured["payload"]["messages"][0]["content"]


def test_network_error_is_fail_safe(monkeypatch):
    monkeypatch.setenv("CYED_LLM_ENABLED", "1")
    monkeypatch.setenv("CYED_ANTHROPIC_API_KEY", "test-key")

    def boom(payload, api_key, timeout=30):
        raise ConnectionError("unreachable")

    with patch.object(llm, "_post", side_effect=boom):
        assert llm.generate(question="q", context="c") is None


def test_enabled_end_to_end_uses_llm_in_tutor(monkeypatch, db):
    """When the LLM is enabled, the tutor uses its answer (not the fallback)."""
    import uuid

    monkeypatch.setenv("CYED_LLM_ENABLED", "1")
    monkeypatch.setenv("CYED_ANTHROPIC_API_KEY", "test-key")

    from products.cyed.ai_agents import tutor
    from products.cyed.ai_agents.models import AgentDefinition
    from products.cyed.curriculum.models import CurriculumOutcome

    tenant = uuid.uuid4()
    AgentDefinition.objects.create(tenant_id=tenant, key="cyed.tutor", name="Tutor", capability="tutor")
    CurriculumOutcome.objects.create(
        tenant_id=tenant, code="AC9M8N01", learning_area="Mathematics", year_level=8,
        content_description="Recognise irrational numbers.",
    )

    with patch.object(llm, "_post", return_value={"content": [{"type": "text", "text": "LLM grounded answer."}]}):
        result = tutor.ask(tenant_id=tenant, question="Explain irrational numbers", year_level=8)

    assert result["grounded"] is True
    assert result["answer"] == "LLM grounded answer."
