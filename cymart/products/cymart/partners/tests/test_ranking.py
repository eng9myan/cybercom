import pytest
from rest_framework.test import APIClient

from products.cymart.partners.models import Partner, PartnerCallLog
from products.cymart.partners.ranking import PartnerRanker

KETO = {"code": "keto", "max_item_carbs_g": 15}


def _item(item_id, calories=400, carbs=5, ingredients=("chicken",), tags=("keto",), relevance=None):
    d = {"item_id": item_id, "calories": calories, "carbs_g": carbs,
         "ingredients": list(ingredients), "diet_tags": list(tags)}
    if relevance is not None:
        d["relevance"] = relevance
    return d


class TestRanker:
    def test_blocked_items_are_excluded_with_code(self):
        profile = {"allergies": ["peanut"], "regimes": [KETO]}
        items = [_item("ok"), _item("satay", ingredients=("chicken", "peanut sauce"))]
        r = PartnerRanker().rank(profile, items)
        assert [i.item_id for i in r.ranked] == ["ok"]
        assert r.excluded == [{"item_id": "satay", "code": "allergen_conflict", "severity": "hard_block"}]

    def test_allergen_never_ranked_even_in_coach_mode(self):
        profile = {"allergies": ["peanut"], "strictness": "coach"}
        r = PartnerRanker().rank(profile, [_item("satay", ingredients=("peanut",))])
        assert r.ranked == []
        assert r.excluded[0]["severity"] == "hard_block"

    def test_full_fit_ranks_before_warning(self):
        profile = {"regimes": [KETO], "remaining_calories": 500, "strictness": "balanced"}
        items = [_item("too-big", calories=900, carbs=1), _item("fits", calories=400, carbs=14)]
        r = PartnerRanker().rank(profile, items)
        assert [i.item_id for i in r.ranked] == ["fits", "too-big"]
        assert [i.severity for i in r.ranked] == ["allow", "warn"]

    def test_include_warnings_false_drops_warned_items(self):
        profile = {"regimes": [KETO], "remaining_calories": 500}
        items = [_item("too-big", calories=900), _item("fits", calories=400)]
        r = PartnerRanker().rank(profile, items, include_warnings=False)
        assert [i.item_id for i in r.ranked] == ["fits"]
        assert r.excluded[0]["item_id"] == "too-big"

    def test_strict_mode_excludes_what_balanced_would_warn(self):
        profile = {"regimes": [KETO], "remaining_calories": 500, "strictness": "strict"}
        r = PartnerRanker().rank(profile, [_item("too-big", calories=900)])
        assert r.ranked == []
        assert r.excluded[0]["code"] == "calorie_budget_exceeded"

    def test_more_carb_headroom_scores_higher(self):
        profile = {"regimes": [KETO]}
        items = [_item("a", carbs=12), _item("b", carbs=3)]
        r = PartnerRanker().rank(profile, items)
        assert [i.item_id for i in r.ranked] == ["b", "a"]
        assert r.ranked[0].fit_score > r.ranked[1].fit_score

    def test_meal_target_prefers_closer_calories(self):
        profile = {"meal_calories_target": 500, "remaining_calories": 900}
        items = [_item("far", calories=850, tags=()), _item("near", calories=480, tags=())]
        r = PartnerRanker().rank(profile, items)
        assert [i.item_id for i in r.ranked] == ["near", "far"]

    def test_relevance_breaks_ties_only(self):
        profile = {"regimes": [KETO]}
        items = [_item("low", carbs=5, relevance=1), _item("high", carbs=5, relevance=9)]
        r = PartnerRanker().rank(profile, items)
        assert [i.item_id for i in r.ranked] == ["high", "low"]

    def test_relevance_does_not_beat_a_better_fit(self):
        profile = {"regimes": [KETO]}
        items = [_item("popular", carbs=14, relevance=99), _item("better", carbs=2, relevance=1)]
        r = PartnerRanker().rank(profile, items)
        assert r.ranked[0].item_id == "better"

    def test_stable_order_when_everything_ties(self):
        r = PartnerRanker().rank({}, [_item("x", tags=()), _item("y", tags=()), _item("z", tags=())])
        assert [i.item_id for i in r.ranked] == ["x", "y", "z"]
        assert all(i.fit_score is None for i in r.ranked)

    def test_limit_applies_after_ranking_and_counts_cover_all(self):
        profile = {"regimes": [KETO]}
        items = [_item(f"i{n}", carbs=n) for n in range(10)]
        r = PartnerRanker().rank(profile, items, limit=3)
        assert [i.item_id for i in r.ranked] == ["i0", "i1", "i2"]
        assert [i.rank for i in r.ranked] == [1, 2, 3]
        assert r.fit == 10

    def test_unknown_ingredients_with_allergy_never_reads_as_safe(self):
        profile = {"allergies": ["peanut"], "strictness": "balanced"}
        unknown = {"item_id": "mystery", "calories": 300}
        known = _item("known", tags=())
        r = PartnerRanker().rank(profile, [unknown, known])
        assert [i.item_id for i in r.ranked] == ["known", "mystery"]
        assert r.ranked[1].severity == "warn" and r.ranked[1].code == "ingredients_unknown"

    def test_matches_evaluate_verdicts(self):
        """The filter is exactly as strict as /evaluate/."""
        from products.cymart.partners.engine import PartnerShieldEngine

        profile = {"allergies": ["peanut"], "regimes": [KETO], "remaining_calories": 500}
        items = [_item("a"), _item("b", carbs=40), _item("c", ingredients=("peanut",)),
                 _item("d", calories=800), {"item_id": "e", "calories": 100}]
        ev = {ln.item_id: ln.severity for ln in PartnerShieldEngine().evaluate(profile, items).lines}
        r = PartnerRanker().rank(profile, items)
        kept = {i.item_id: i.severity for i in r.ranked}
        for item_id, sev in ev.items():
            if sev in ("allow", "warn"):
                assert kept[item_id] == sev
            else:
                assert item_id not in kept


@pytest.mark.django_db
class TestRankAPI:
    def _client(self):
        partner, raw = Partner.create_with_key("Rank Platform")
        c = APIClient()
        c.credentials(HTTP_X_API_KEY=raw)
        return c, partner

    def test_requires_api_key(self):
        resp = APIClient().post("/api/v1/partner/rank/", {"profile": {}, "items": [{"item_id": "1"}]}, format="json")
        assert resp.status_code == 403

    def test_returns_ranked_and_excluded_and_counts(self):
        c, _ = self._client()
        body = {
            "profile": {"allergies": ["peanut"], "regimes": [KETO]},
            "items": [_item("a", carbs=9), _item("b", carbs=2),
                      _item("satay", ingredients=("peanut sauce",))],
        }
        resp = c.post("/api/v1/partner/rank/", body, format="json")
        assert resp.status_code == 200
        data = resp.json()
        assert [r["item_id"] for r in data["ranked"]] == ["b", "a"]
        assert data["ranked"][0]["rank"] == 1 and data["ranked"][0]["summary"]
        assert data["excluded"] == [{"item_id": "satay", "code": "allergen_conflict", "severity": "hard_block"}]
        assert data["counts"] == {"evaluated": 3, "fit": 2, "fit_with_warning": 0, "excluded": 1}

    def test_logs_usage(self):
        c, partner = self._client()
        c.post("/api/v1/partner/rank/", {"profile": {}, "items": [_item("a"), _item("b")]}, format="json")
        log = PartnerCallLog.objects.get(partner=partner)
        assert log.item_count == 2

    def test_limit_and_size_validation(self):
        c, _ = self._client()
        too_many = {"profile": {}, "items": [_item(f"i{n}") for n in range(501)]}
        assert c.post("/api/v1/partner/rank/", too_many, format="json").status_code == 400
        bad_limit = {"profile": {}, "items": [_item("a")], "limit": 101}
        assert c.post("/api/v1/partner/rank/", bad_limit, format="json").status_code == 400
        assert c.post("/api/v1/partner/rank/", {"profile": {}, "items": []}, format="json").status_code == 400

    def test_500_items_accepted(self):
        c, _ = self._client()
        body = {"profile": {"regimes": [KETO]}, "items": [_item(f"i{n}", carbs=n % 15) for n in range(500)], "limit": 5}
        resp = c.post("/api/v1/partner/rank/", body, format="json")
        assert resp.status_code == 200
        assert len(resp.json()["ranked"]) == 5
        assert resp.json()["counts"]["evaluated"] == 500

    def test_inactive_partner_rejected(self):
        c, partner = self._client()
        partner.is_active = False
        partner.save()
        resp = c.post("/api/v1/partner/rank/", {"profile": {}, "items": [_item("a")]}, format="json")
        assert resp.status_code == 403
