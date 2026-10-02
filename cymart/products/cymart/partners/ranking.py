"""Filter-and-rank mode: the caller sends many candidate items (for example
everything its own search returned for "burger") and gets back only those
that fit the customer's plan, best fit first.

Reuses the evaluation engine's three gates unchanged, so the filter is
exactly as strict as /evaluate/. Ranking is deliberately simple and
explainable:

    1. Tier   — items that fully fit ("allow") come before items that fit
                with a warning ("warn").
    2. Score  — within a tier, higher ``fit_score`` first (0-100, built only
                from numbers the caller sent; ``None`` when none apply).
    3. Hint   — the caller's own ``relevance`` (e.g. its search score) breaks
                ties, so Diet Shield never overrides the platform's ranking
                between equally good fits.
    4. Order  — original order, so results are stable.

Blocked and hard-blocked items are never ranked; they are reported in
``excluded`` with their reason code so the caller can say why they are hidden.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .engine import PartnerShieldEngine
from .i18n import join_list, normalise, t

_TIER = {"allow": 0, "warn": 1}


@dataclass
class RankedItem:
    item_id: str
    severity: str
    code: str
    reason: str
    fit_score: int | None
    relevance: float | None
    summary: str
    detail: dict
    rank: int = 0


@dataclass
class RankResult:
    ranked: list[RankedItem] = field(default_factory=list)
    excluded: list[dict] = field(default_factory=list)
    evaluated: int = 0
    fit: int = 0
    warned: int = 0


def _fit_components(item: dict, profile: dict, lang: str = "en") -> tuple[list[float], dict, list[str]]:
    """Return (component scores 0-1, structured detail, summary phrases)."""
    comps: list[float] = []
    detail: dict = {}
    phrases: list[str] = []

    calories = float(item.get("calories", 0))
    target = profile.get("meal_calories_target")
    remaining = profile.get("remaining_calories")

    if target:
        target = float(target)
        comps.append(max(0.0, 1 - abs(calories - target) / target))
        detail["calories"] = calories
        detail["meal_calories_target"] = target
        phrases.append(t(lang, "kcal_vs_target", calories=int(calories), target=int(target)))
    if remaining is not None:
        left = float(remaining) - calories
        detail["calories_left_after"] = left
        if not target:
            phrases.append(t(lang, "leaves_kcal", left=int(left)))

    carbs = float(item.get("carbs_g", 0))
    for regime in profile.get("regimes") or []:
        limit = regime.get("max_item_carbs_g")
        if limit:
            limit = float(limit)
            comps.append(max(0.0, min(1.0, 1 - carbs / limit)))
            detail.setdefault("carb_headroom_g", {})[str(regime.get("code", ""))] = limit - carbs
            phrases.append(t(lang, "carbs_vs_limit", carbs=f"{carbs:g}", limit=f"{limit:g}"))
    return comps, detail, phrases


class PartnerRanker:
    def __init__(self, lang: str = "en"):
        self.lang = lang if lang in ("en", "ar") else "en"

    def rank(
        self,
        profile: dict,
        items: list[dict],
        limit: int = 20,
        include_warnings: bool = True,
    ) -> RankResult:
        engine = PartnerShieldEngine(self.lang)
        regimes = profile.get("regimes") or []

        result = RankResult(evaluated=len(items))
        candidates: list[tuple[tuple, RankedItem]] = []

        for position, item in enumerate(items):
            v = engine.check_item(profile, item)
            if v.severity not in _TIER or (v.severity == "warn" and not include_warnings):
                result.excluded.append({"item_id": v.item_id, "code": v.code, "severity": v.severity})
                continue

            comps, detail, phrases = _fit_components(item, profile, self.lang)
            score = round(100 * sum(comps) / len(comps)) if comps else None
            matched_tags = sorted(
                {str(r.get("code", "")).lower() for r in regimes}
                & {normalise(tag) for tag in item.get("diet_tags") or []}
            )
            if matched_tags:
                detail["tags_matched"] = matched_tags
                phrases.insert(0, t(self.lang, "tag_compatible", tags="/".join(matched_tags)))
            detail_text = join_list(self.lang, phrases)
            if v.severity == "allow":
                summary = detail_text or t(self.lang, "ok")
            else:
                summary = f"{v.reason} {detail_text}".strip()

            relevance = item.get("relevance")
            entry = RankedItem(
                item_id=v.item_id, severity=v.severity, code=v.code, reason=v.reason,
                fit_score=score, relevance=relevance, summary=summary, detail=detail,
            )
            key = (_TIER[v.severity], -(score if score is not None else 0),
                   -(float(relevance) if relevance is not None else 0.0), position)
            candidates.append((key, entry))

        candidates.sort(key=lambda kv: kv[0])
        result.fit = sum(1 for _, e in candidates if e.severity == "allow")
        result.warned = len(candidates) - result.fit
        for i, (_, entry) in enumerate(candidates[:limit], start=1):
            entry.rank = i
            result.ranked.append(entry)
        return result
