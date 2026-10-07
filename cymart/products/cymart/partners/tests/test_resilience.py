"""A slow or dead model must never take the safety checks down with it (found by simulation/sim_availability.py)."""
import threading
import time

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from products.cymart.partners.agent import views as agent_views
from products.cymart.partners.agent.providers.base import CompletionProvider
from products.cymart.partners.agent.providers.claude import ClaudeCompletionProvider
from products.cymart.partners.models import Partner

MSG = {"profile": {}, "messages": [{"role": "user", "content": "hello"}]}
EVAL = {"profile": {"allergies": ["peanut"]}, "items": [{"item_id": "x", "ingredients": ["rice"]}]}


@pytest.fixture(autouse=True)
def _clean():
    cache.clear()


def client():
    _, raw = Partner.create_with_key("Resilience")
    c = APIClient()
    c.credentials(HTTP_X_API_KEY=raw)
    return c


class TestAdapterClient:
    def test_one_shared_client_with_bounded_waits(self, monkeypatch):
        pytest.importorskip("anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k-test-resilience")
        monkeypatch.delenv("DIET_SHIELD_AGENT_TIMEOUT", raising=False)
        monkeypatch.delenv("DIET_SHIELD_AGENT_RETRIES", raising=False)
        a, b = ClaudeCompletionProvider()._client(), ClaudeCompletionProvider()._client()
        assert a is b                                  # connection reuse across requests
        assert a.timeout == 25.0 and a.max_retries == 1

    def test_limits_can_be_changed_by_environment(self, monkeypatch):
        pytest.importorskip("anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "k-test-resilience-2")
        monkeypatch.setenv("DIET_SHIELD_AGENT_TIMEOUT", "7")
        monkeypatch.setenv("DIET_SHIELD_AGENT_RETRIES", "0")
        c = ClaudeCompletionProvider()._client()
        assert c.timeout == 7.0 and c.max_retries == 0


@pytest.mark.django_db
class TestBulkhead:
    def test_when_all_assistant_slots_are_busy_the_turn_is_refused_quickly_and_checks_still_work(self, monkeypatch):
        slots = threading.BoundedSemaphore(1)
        monkeypatch.setattr(agent_views, "_slots", slots)
        c = client()
        slots.acquire()                                # a hung turn is holding the only slot
        t0 = time.perf_counter()
        r = c.post("/api/v1/partner/agent/turn/", MSG, format="json")
        assert r.status_code == 503 and r.json()["error"] == "agent_busy"
        assert time.perf_counter() - t0 < 3
        assert c.post("/api/v1/partner/evaluate/", EVAL, format="json").status_code == 200       # the checks are untouched
        slots.release()
        assert c.post("/api/v1/partner/agent/turn/", MSG, format="json").status_code == 200

    def test_the_slot_is_returned_even_when_the_model_fails(self, monkeypatch, settings):
        slots = threading.BoundedSemaphore(1)
        monkeypatch.setattr(agent_views, "_slots", slots)
        settings.AGENT_PROVIDER = "products.cymart.partners.tests.test_resilience.Exploding"
        c = client()
        assert c.post("/api/v1/partner/agent/turn/", MSG, format="json").status_code == 503
        assert slots.acquire(blocking=False)           # not leaked
        slots.release()


class Exploding(CompletionProvider):
    def complete(self, *a, **k):
        raise RuntimeError("model down")


@pytest.mark.django_db
class TestMeteringNeverFailsARequest:
    """A failed usage-log write must not turn a safety answer into a 500 (found by running 20,000 questions on SQLite)."""

    @pytest.fixture
    def broken_log(self, monkeypatch):
        from products.cymart.partners.models import PartnerCallLog

        def boom(*a, **k):
            raise RuntimeError("database is locked")
        monkeypatch.setattr(PartnerCallLog.objects, "create", boom)

    def test_every_endpoint_still_answers(self, broken_log):
        c = client()
        item = {"item_id": "x", "calories": 100, "carbs_g": 1, "ingredients": ["rice"], "diet_tags": []}
        assert c.post("/api/v1/partner/evaluate/", EVAL, format="json").status_code == 200
        assert c.post("/api/v1/partner/rank/", {"profile": {}, "items": [item]}, format="json").status_code == 200
        assert c.post("/api/v1/partner/prepare/", {"profile": {}, "items": [item]}, format="json").status_code == 200
        assert c.post("/api/v1/partner/agent/turn/", MSG, format="json").status_code == 200
        assert c.post("/api/v1/partner/plan/targets/", {"intake": {"sex": "male", "age": 30, "height_cm": 180, "weight_kg": 80}}, format="json").status_code == 200

    def test_the_failure_is_logged_for_reconciliation(self, broken_log, caplog):
        import logging
        with caplog.at_level(logging.ERROR, logger="products.cymart.partners.metering"):
            client().post("/api/v1/partner/evaluate/", EVAL, format="json")
        assert "usage metering failed" in caplog.text