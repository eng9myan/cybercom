import uuid

import pytest
from rest_framework.test import APIClient


def _authed_client(mint_token, mock_jwks, user_id):
    client = APIClient()
    token = mint_token({"sub": str(user_id), "roles": ["customer"], "permissions": []})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestAgentMessageAPI:
    def test_requires_auth(self):
        resp = APIClient().post("/api/v1/agent/message/", {"text": "hi"}, format="json")
        assert resp.status_code in (401, 403)

    def test_message_returns_reply(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.post("/api/v1/agent/message/", {"text": "hi"}, format="json")
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert "reply" in body and "tool_calls" in body

    def test_off_topic_message_is_declined(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.post(
            "/api/v1/agent/message/", {"text": "what's today's weather?"}, format="json"
        )
        assert resp.status_code == 200
        assert "CyMart ordering" in resp.json()["reply"]

    def test_conversation_is_scoped_per_caller(self, mint_token, mock_jwks):
        from products.cymart.agent.models import AgentMessage

        a, b = uuid.uuid4(), uuid.uuid4()
        _authed_client(mint_token, mock_jwks, a).post(
            "/api/v1/agent/message/", {"text": "hello from a"}, format="json"
        )
        _authed_client(mint_token, mock_jwks, b).post(
            "/api/v1/agent/message/", {"text": "hello from b"}, format="json"
        )
        assert AgentMessage.objects.filter(customer_id=a).count() == 2  # user + assistant
        assert AgentMessage.objects.filter(customer_id=b).count() == 2

    def test_blank_text_is_rejected(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.post("/api/v1/agent/message/", {"text": ""}, format="json")
        assert resp.status_code == 400
