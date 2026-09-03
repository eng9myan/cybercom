"""
Tests for NphiesClient OAuth2 client-credentials token handling.

The production client
(``products.cymed.integrations.nphies.client.NphiesClient``) uses
``httpx``. Each test injects a mock ``httpx.Client`` and asserts that:

* the first call to ``_token()`` hits the auth endpoint,
* the token is cached with TTL = (expires_in - 60) — i.e. the
  "55min-cached" behaviour promised by the spec (with a 3300s
  ``expires_in``, the cache TTL is 3240s = 54 min, well under the
  token's lifetime), and
* once the cache expires (simulated by clearing it), the client renews.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.delete("nphies:token")
    yield
    cache.delete("nphies:token")


@pytest.fixture
def nphies_env(monkeypatch):
    monkeypatch.setenv("NPHIES_BASE_URL", "https://sandbox.nphies.sa")
    monkeypatch.setenv("NPHIES_AUTH_URL",
                       "https://sandbox.nphies.sa/oauth2/token")
    monkeypatch.setenv("NPHIES_CLIENT_ID", "cymed-test")
    monkeypatch.setenv("NPHIES_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("NPHIES_SCOPES", "nphies")
    monkeypatch.setenv("NPHIES_LICENSEE_ID", "10000000123456")
    monkeypatch.setenv("NPHIES_MTLS_CERT_PATH", "")
    monkeypatch.setenv("NPHIES_MTLS_KEY_PATH", "")


def _mock_client(*, token: str = "test-access-token",
                  expires_in: int = 3300) -> MagicMock:
    """Return a ``MagicMock`` shaped like ``httpx.Client`` returning a token."""
    fake = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": token,
                                "expires_in": expires_in,
                                "token_type": "Bearer"}
    resp.raise_for_status.return_value = None
    fake.post.return_value = resp
    return fake


def test_token_is_cached_across_calls(nphies_env):
    """Second _token() call within the cache TTL must NOT hit the network."""
    from products.cymed.integrations.nphies.client import NphiesClient

    mock = _mock_client()
    client = NphiesClient(client=mock)

    first = client._token()
    second = client._token()

    assert first == "test-access-token"
    assert second == "test-access-token"
    assert mock.post.call_count == 1, (
        "expected the second call to hit the cache, not the auth endpoint"
    )


def test_token_ttl_matches_expires_in_minus_60(nphies_env, mocker):
    """cache.set must be called with ttl = expires_in - 60 (55min buffer)."""
    from products.cymed.integrations.nphies.client import NphiesClient

    cache_set = mocker.spy(cache, "set")

    NphiesClient(client=_mock_client(expires_in=3300))._token()

    assert cache_set.call_count == 1
    args, _ = cache_set.call_args
    key, value, ttl = args
    assert key == "nphies:token"
    assert value == "test-access-token"
    assert ttl == 3300 - 60, "TTL must include a 60s renewal buffer"


def test_token_renews_after_expiry(nphies_env):
    """
    Simulate token expiry by clearing the cache; the next call must re-hit
    the auth endpoint and pick up the fresh token value.
    """
    from products.cymed.integrations.nphies.client import NphiesClient

    fake = MagicMock()
    responses = [
        {"access_token": "token-A", "expires_in": 3300,
         "token_type": "Bearer"},
        {"access_token": "token-B", "expires_in": 3300,
         "token_type": "Bearer"},
    ]

    def _post(*_args, **_kwargs):
        body = responses.pop(0)
        r = MagicMock()
        r.json.return_value = body
        r.raise_for_status.return_value = None
        return r

    fake.post.side_effect = _post
    client = NphiesClient(client=fake)

    assert client._token() == "token-A"
    cache.delete("nphies:token")
    assert client._token() == "token-B"
    assert fake.post.call_count == 2


def test_token_request_carries_client_credentials_and_scope(nphies_env):
    from products.cymed.integrations.nphies.client import NphiesClient

    mock = _mock_client()
    NphiesClient(client=mock)._token()

    call = mock.post.call_args
    assert call.args[0] == "https://sandbox.nphies.sa/oauth2/token"
    assert call.kwargs["data"]["grant_type"] == "client_credentials"
    assert call.kwargs["data"]["scope"] == "nphies"
    assert call.kwargs["auth"] == ("cymed-test", "test-secret")


def test_headers_include_bearer_token(nphies_env):
    from products.cymed.integrations.nphies.client import NphiesClient

    headers = NphiesClient(client=_mock_client(token="tok-xyz"))._headers()

    assert headers["Authorization"] == "Bearer tok-xyz"
    assert headers["Content-Type"] == "application/fhir+json"
    assert headers["Accept"] == "application/fhir+json"


def test_base_url_defaults_to_sandbox(monkeypatch):
    monkeypatch.delenv("NPHIES_BASE_URL", raising=False)
    from products.cymed.integrations.nphies.client import NphiesClient

    assert NphiesClient().base_url == "https://sandbox.nphies.sa"
