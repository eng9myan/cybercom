"""
Real OAuth2 client_credentials exchange for WHO's ICD-11 API — WHO issues
short-lived access tokens (~1h), not a static bearer token, so this must
fetch, cache, and refresh, not just read a value out of settings once.
Mocks only the HTTP boundary (WHO's real token/search endpoints), same
discipline as every other cross-service mock in this repo.
"""

from unittest.mock import Mock, patch

import pytest

from platform.terminology.providers import icd11


@pytest.fixture(autouse=True)
def _reset_caches():
    icd11.reset_token_cache()
    icd11.reset_search_cache()
    yield
    icd11.reset_token_cache()
    icd11.reset_search_cache()


class TestICD11OAuthExchange:
    @pytest.fixture(autouse=True)
    def _icd11_credentials(self, settings):
        # pytest-django's `settings` fixture — real per-test override,
        # auto-reverted after each test. override_settings as a class
        # decorator only works on Django's own SimpleTestCase, not plain
        # pytest classes, which is the convention used everywhere else in
        # this repo's test suite. Scoped to this class only (defined
        # inside it) — TestICD11NoCredentialsConfigured below needs the
        # real empty defaults, not these.
        settings.ICD11_CLIENT_ID = "test-client"
        settings.ICD11_CLIENT_SECRET = "test-secret"

    @patch("platform.terminology.providers.icd11.httpx.Client")
    def test_search_exchanges_token_then_calls_search_api(self, mock_client_cls):
        token_response = Mock(status_code=200, json=lambda: {"access_token": "real-tok", "expires_in": 3600})
        search_response = Mock(
            status_code=200,
            json=lambda: {"destinationEntities": [{"theCode": "1B10.0", "title": "Type 1 diabetes mellitus", "id": "x"}]},
        )
        mock_client = Mock()
        mock_client.post.return_value = token_response
        mock_client.get.return_value = search_response
        mock_client_cls.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = Mock(return_value=False)

        provider = icd11.ICD11Provider()
        results = provider.search("diabetes")

        assert results == [{"code": "1B10.0", "display": "Type 1 diabetes mellitus", "type": "stem", "id": "x"}]

        # Real token exchange happened, with the real WHO endpoint/grant shape.
        token_call = mock_client.post.call_args
        assert token_call[0][0] == icd11.ICD11_TOKEN_URL
        assert token_call[1]["data"]["grant_type"] == "client_credentials"
        assert token_call[1]["data"]["client_id"] == "test-client"
        assert token_call[1]["data"]["client_secret"] == "test-secret"

        # Real search call carried the exchanged token, not the client secret.
        search_call = mock_client.get.call_args
        assert search_call[1]["headers"]["Authorization"] == "Bearer real-tok"

    @patch("platform.terminology.providers.icd11.httpx.Client")
    def test_token_is_cached_across_multiple_searches(self, mock_client_cls):
        token_response = Mock(status_code=200, json=lambda: {"access_token": "cached-tok", "expires_in": 3600})
        search_response = Mock(status_code=200, json=lambda: {"destinationEntities": []})
        mock_client = Mock()
        mock_client.post.return_value = token_response
        mock_client.get.return_value = search_response
        mock_client_cls.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = Mock(return_value=False)

        provider = icd11.ICD11Provider()
        provider.search("diabetes")
        provider.search("osteoarthritis")

        # One token exchange, two real search calls — not re-authenticating every request.
        assert mock_client.post.call_count == 1
        assert mock_client.get.call_count == 2

    @patch("platform.terminology.providers.icd11.httpx.Client")
    def test_expired_token_is_refreshed(self, mock_client_cls):
        token_response = Mock(status_code=200, json=lambda: {"access_token": "short-lived", "expires_in": 30})
        search_response = Mock(status_code=200, json=lambda: {"destinationEntities": []})
        mock_client = Mock()
        mock_client.post.return_value = token_response
        mock_client.get.return_value = search_response
        mock_client_cls.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = Mock(return_value=False)

        provider = icd11.ICD11Provider()
        provider.search("diabetes")
        # expires_in=30 minus the 60s safety margin means the cached token
        # is already treated as expired for the very next call — forces a
        # real re-exchange rather than reusing a token WHO would reject.
        provider.search("diabetes")

        assert mock_client.post.call_count == 2

    @patch("platform.terminology.providers.icd11.httpx.Client")
    def test_token_endpoint_failure_falls_back_to_mock_data(self, mock_client_cls):
        mock_client = Mock()
        mock_client.post.return_value = Mock(status_code=401, json=lambda: {"error": "invalid_client"})
        mock_client_cls.return_value.__enter__ = Mock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = Mock(return_value=False)

        provider = icd11.ICD11Provider()
        results = provider.search("diabetes")

        # Real fallback seed data, not an empty list or a raised exception.
        assert any(r["code"] == "1B10.0" for r in results)
        mock_client.get.assert_not_called()  # never reached the search API with no valid token


class TestICD11NoCredentialsConfigured:
    def test_search_falls_back_without_making_any_http_call(self):
        # No override_settings here — ICD11_CLIENT_ID/SECRET are empty by
        # default (core/settings_test.py inherits core/settings.py's ""
        # defaults), matching a real deployment that hasn't registered yet.
        with patch("platform.terminology.providers.icd11.httpx.Client") as mock_client_cls:
            provider = icd11.ICD11Provider()
            results = provider.search("diabetes")
            mock_client_cls.assert_not_called()
        assert any(r["code"] == "1B10.0" for r in results)
