import io

import pytest
from django.core.cache import cache
from django.core.management import call_command
from rest_framework.test import APIClient

from products.cymart.partners.models import Partner, PartnerCallLog

BODY = {"profile": {"allergies": ["peanut"]}, "items": [{"item_id": "x", "ingredients": ["rice"]}]}


@pytest.fixture(autouse=True)
def _clean_cache():
    cache.clear()
    yield
    cache.clear()


def client_for(name):
    _, raw = Partner.create_with_key(name)
    c = APIClient()
    c.credentials(HTTP_X_API_KEY=raw)
    return c


@pytest.mark.django_db
class TestRateLimits:
    def test_over_the_limit_is_429_with_retry_after(self, settings):
        settings.RATE_LIMIT_PARTNER = "3/min"
        c = client_for("A")
        assert [c.post("/api/v1/partner/evaluate/", BODY, format="json").status_code for _ in range(3)] == [200, 200, 200]
        r = c.post("/api/v1/partner/evaluate/", BODY, format="json")
        assert r.status_code == 429 and "Retry-After" in r

    def test_limit_is_per_partner(self, settings):
        settings.RATE_LIMIT_PARTNER = "2/min"
        a, b = client_for("A"), client_for("B")
        for _ in range(2):
            a.post("/api/v1/partner/evaluate/", BODY, format="json")
        assert a.post("/api/v1/partner/evaluate/", BODY, format="json").status_code == 429
        assert b.post("/api/v1/partner/evaluate/", BODY, format="json").status_code == 200

    def test_every_endpoint_shares_the_partner_allowance(self, settings):
        settings.RATE_LIMIT_PARTNER = "2/min"
        c = client_for("A")
        c.post("/api/v1/partner/evaluate/", BODY, format="json")
        c.post("/api/v1/partner/rank/", BODY, format="json")
        assert c.post("/api/v1/partner/prepare/", BODY, format="json").status_code == 429

    def test_agent_has_its_own_tighter_limit(self, settings):
        settings.RATE_LIMIT_AGENT = "2/min"
        c = client_for("A")
        msg = {"profile": {}, "messages": [{"role": "user", "content": "hello"}]}
        assert [c.post("/api/v1/partner/agent/turn/", msg, format="json").status_code for _ in range(2)] == [200, 200]
        assert c.post("/api/v1/partner/agent/turn/", msg, format="json").status_code == 429
        assert c.post("/api/v1/partner/evaluate/", BODY, format="json").status_code == 200       # other endpoints unaffected

    def test_planner_endpoints_are_limited_too(self, settings):
        settings.RATE_LIMIT_PARTNER = "1/min"
        c = client_for("A")
        intake = {"intake": {"sex": "male", "age": 30, "height_cm": 175, "weight_kg": 80}}
        assert c.post("/api/v1/partner/plan/targets/", intake, format="json").status_code == 200
        assert c.post("/api/v1/partner/plan/targets/", intake, format="json").status_code == 429

    def test_unauthenticated_calls_are_refused_not_counted(self, settings):
        settings.RATE_LIMIT_PARTNER = "1/min"
        anon = APIClient()
        assert [anon.post("/api/v1/partner/evaluate/", BODY, format="json").status_code for _ in range(3)] == [403, 403, 403]

    def test_default_allowance_is_generous(self):
        c = client_for("A")
        assert all(c.post("/api/v1/partner/evaluate/", BODY, format="json").status_code == 200 for _ in range(30))


@pytest.mark.django_db
class TestOperatorCommands:
    def test_deactivate_by_name_blocks_the_key_immediately(self):
        c = client_for("Local test")
        assert c.post("/api/v1/partner/evaluate/", BODY, format="json").status_code == 200
        out = io.StringIO()
        call_command("deactivate_partner", "Local test", stdout=out)
        assert "Deactivated: Local test" in out.getvalue()
        assert c.post("/api/v1/partner/evaluate/", BODY, format="json").status_code == 403

    def test_deactivate_by_key_prefix(self):
        p, raw = Partner.create_with_key("By prefix")
        call_command("deactivate_partner", raw[:14], stdout=io.StringIO())
        p.refresh_from_db()
        assert p.is_active is False

    def test_deactivate_unknown_is_an_error(self):
        from django.core.management.base import CommandError
        with pytest.raises(CommandError):
            call_command("deactivate_partner", "nobody", stdout=io.StringIO())

    def test_usage_report_counts_calls_and_items(self):
        c = client_for("Reported")
        c.post("/api/v1/partner/evaluate/", {**BODY, "items": [{"item_id": str(i)} for i in range(5)]}, format="json")
        c.post("/api/v1/partner/evaluate/", BODY, format="json")
        out = io.StringIO()
        call_command("usage_report", "--days", "7", stdout=out)
        text = out.getvalue()
        assert "Reported" in text
        row = next(l for l in text.splitlines() if "Reported" in l)
        assert row.split()[-2:] == ["2", "6"]            # 2 calls, 6 items

    def test_usage_report_with_no_usage(self):
        out = io.StringIO()
        call_command("usage_report", stdout=out)
        assert "No usage" in out.getvalue()
        assert PartnerCallLog.objects.count() == 0
