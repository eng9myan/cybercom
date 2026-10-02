import pytest
from rest_framework.test import APIClient

from products.cymart.partners.models import Partner, PartnerCallLog


@pytest.mark.django_db
class TestPartnerEvaluateAPI:
    def test_requires_api_key(self):
        client = APIClient()
        resp = client.post(
            "/api/v1/partner/evaluate/",
            {"profile": {}, "items": [{"item_id": "1", "calories": 400}]},
            format="json",
        )
        assert resp.status_code in (401, 403)

    def test_rejects_invalid_api_key(self):
        client = APIClient()
        client.credentials(HTTP_X_API_KEY="not-a-real-key")
        resp = client.post(
            "/api/v1/partner/evaluate/",
            {"profile": {}, "items": [{"item_id": "1", "calories": 400}]},
            format="json",
        )
        assert resp.status_code == 403

    def test_valid_key_evaluates_and_logs_usage(self):
        partner, raw_key = Partner.create_with_key("Test Platform")
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=raw_key)
        resp = client.post(
            "/api/v1/partner/evaluate/",
            {
                "profile": {"allergies": ["peanut"], "strictness": "strict"},
                "items": [
                    {"item_id": "a1", "calories": 400, "ingredients": ["chicken"]},
                    {"item_id": "a2", "calories": 300, "ingredients": ["peanut sauce"]},
                ],
            },
            format="json",
        )
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body["overall"] == "hard_block"
        assert len(body["lines"]) == 2
        assert PartnerCallLog.objects.filter(partner=partner, item_count=2).exists()

    def test_response_includes_code_matched_and_swap(self):
        _, raw_key = Partner.create_with_key("Swap Platform")
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=raw_key)
        resp = client.post(
            "/api/v1/partner/evaluate/",
            {
                "profile": {"allergies": ["peanut"], "strictness": "strict"},
                "items": [
                    {
                        "item_id": "satay",
                        "ingredients": ["chicken", "peanut sauce"],
                        "alternatives": [
                            {"item_id": "shawarma", "ingredients": ["chicken", "garlic sauce"]},
                        ],
                    }
                ],
            },
            format="json",
        )
        assert resp.status_code == 200, resp.content
        line = resp.json()["lines"][0]
        assert line["code"] == "allergen_conflict"
        assert line["matched"] == ["peanut"]
        assert line["swap"] == {"item_id": "shawarma"}

    def test_too_many_alternatives_rejected(self):
        _, raw_key = Partner.create_with_key("Alt Platform")
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=raw_key)
        resp = client.post(
            "/api/v1/partner/evaluate/",
            {
                "profile": {},
                "items": [
                    {"item_id": "x", "alternatives": [{"item_id": str(i)} for i in range(6)]}
                ],
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_inactive_partner_is_rejected(self):
        partner, raw_key = Partner.create_with_key("Suspended Platform")
        partner.is_active = False
        partner.save()
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=raw_key)
        resp = client.post(
            "/api/v1/partner/evaluate/",
            {"profile": {}, "items": [{"item_id": "1"}]},
            format="json",
        )
        assert resp.status_code == 403

    def test_too_many_items_rejected(self):
        partner, raw_key = Partner.create_with_key("Bulk Platform")
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=raw_key)
        resp = client.post(
            "/api/v1/partner/evaluate/",
            {"profile": {}, "items": [{"item_id": str(i)} for i in range(101)]},
            format="json",
        )
        assert resp.status_code == 400

    def test_two_partners_are_fully_isolated(self):
        _, key_a = Partner.create_with_key("Platform A")
        partner_b, key_b = Partner.create_with_key("Platform B")
        client = APIClient()
        client.credentials(HTTP_X_API_KEY=key_a)
        client.post("/api/v1/partner/evaluate/", {"profile": {}, "items": [{"item_id": "1"}]}, format="json")
        # Platform B's key must never see Platform A's usage.
        assert PartnerCallLog.objects.filter(partner=partner_b).count() == 0


@pytest.mark.django_db
class TestPartnerLaneIsSeparateFromCustomerAuth:
    def test_customer_jwt_does_not_work_on_partner_endpoint(self, mint_token, mock_jwks):
        client = APIClient()
        token = mint_token({"sub": "some-customer", "roles": ["customer"], "permissions": []})
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = client.post(
            "/api/v1/partner/evaluate/",
            {"profile": {}, "items": [{"item_id": "1"}]},
            format="json",
        )
        assert resp.status_code in (401, 403)
