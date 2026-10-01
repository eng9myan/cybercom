import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cymart.dietshield.models import DietProfile, NutritionFact


def _authed_client(mint_token, mock_jwks, user_id):
    client = APIClient()
    token = mint_token({"sub": str(user_id), "roles": ["customer"], "permissions": []})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestDietShieldAPI:
    def test_profile_requires_auth(self):
        resp = APIClient().get("/api/v1/dietshield/profile/")
        assert resp.status_code in (401, 403)

    def test_no_profile_returns_404(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.get("/api/v1/dietshield/profile/")
        assert resp.status_code == 404

    def test_create_profile_builds_plan(self, mint_token, mock_jwks):
        user_id = uuid.uuid4()
        client = _authed_client(mint_token, mock_jwks, user_id)
        resp = client.post(
            "/api/v1/dietshield/profile/",
            {
                "sex": "male", "age": 34, "height_cm": "178", "weight_kg": "92",
                "activity_level": "sedentary", "goal_type": "lose",
                "weekly_pace_kg": "0.5", "strictness": "balanced",
                "regime_codes": ["keto"],
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        body = resp.json()
        assert body["plan"]["daily_calories"] > 0
        assert DietProfile.objects.filter(customer_id=user_id).exists()

    def test_profile_is_scoped_to_caller(self, mint_token, mock_jwks):
        a, b = uuid.uuid4(), uuid.uuid4()
        client_a = _authed_client(mint_token, mock_jwks, a)
        client_a.post(
            "/api/v1/dietshield/profile/",
            {"sex": "female", "age": 28, "height_cm": "165", "weight_kg": "60",
             "activity_level": "light", "goal_type": "maintain", "weekly_pace_kg": "0.5"},
            format="json",
        )
        client_b = _authed_client(mint_token, mock_jwks, b)
        resp = client_b.get("/api/v1/dietshield/profile/")
        assert resp.status_code == 404

    def test_regimes_list(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.get("/api/v1/dietshield/regimes/")
        assert resp.status_code == 200
        codes = {r["code"] for r in resp.json()}
        assert "keto" in codes and "halal" in codes

    def test_evaluate_without_profile_allows(self, mint_token, mock_jwks):
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.post(
            "/api/v1/dietshield/evaluate/",
            {"items": [{"product_id": str(uuid.uuid4()), "quantity": "1"}]},
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["shield_active"] is False
        assert body["overall"] == "ALLOW"

    def test_evaluate_blocks_off_plan_item(self, mint_token, mock_jwks):
        user_id = uuid.uuid4()
        client = _authed_client(mint_token, mock_jwks, user_id)
        client.post(
            "/api/v1/dietshield/profile/",
            {"sex": "male", "age": 40, "height_cm": "180", "weight_kg": "90",
             "activity_level": "moderate", "goal_type": "maintain",
             "weekly_pace_kg": "0.5", "strictness": "strict", "regime_codes": ["keto"]},
            format="json",
        )
        bad_product = uuid.uuid4()
        NutritionFact.objects.create(
            product_id=bad_product, calories=Decimal("820"), carbs_g=Decimal("82"),
            ingredients=["wheat"],
        )
        resp = client.post(
            "/api/v1/dietshield/evaluate/",
            {"items": [{"product_id": str(bad_product), "quantity": "1"}]},
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["shield_active"] is True
        assert body["overall"] == "BLOCK"
        assert body["allowed"] is False

    def test_today_status_after_profile(self, mint_token, mock_jwks):
        user_id = uuid.uuid4()
        client = _authed_client(mint_token, mock_jwks, user_id)
        client.post(
            "/api/v1/dietshield/profile/",
            {"sex": "female", "age": 30, "height_cm": "165", "weight_kg": "65",
             "activity_level": "light", "goal_type": "lose", "weekly_pace_kg": "0.5"},
            format="json",
        )
        resp = client.get("/api/v1/dietshield/today/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["consumed_calories"] == 0
        assert body["remaining_calories"] == body["daily_calories"]
