"""
Curriculum retrieval for the CyEd tutor (RAG grounding).

Ranks ACARA CurriculumOutcome records against a natural-language question so the
tutor can answer *only* from retrieved, cited curriculum — never free-form. This
is deliberately a simple, DB-portable term-overlap ranker (works on SQLite and
Postgres); swap in Postgres full-text / pgvector for scale without changing the
caller contract.
"""

import re

from products.cyed.curriculum.models import CurriculumOutcome

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "what", "how", "why", "do", "does", "can", "i", "you", "with", "my", "me",
    "explain", "tell", "about", "help", "please", "this", "that",
}

_CODE_RE = re.compile(r"\bAC9[A-Z0-9]+\b", re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    words = re.split(r"[^a-zA-Z0-9]+", (text or "").lower())
    return [w for w in words if len(w) >= 3 and w not in _STOPWORDS]


def _score(outcome: CurriculumOutcome, tokens: list[str]) -> int:
    haystacks = {
        "code": (outcome.code or "").lower(),
        "area": (outcome.learning_area or "").lower(),
        "subject": (outcome.subject or "").lower(),
        "strand": f"{outcome.strand} {outcome.sub_strand}".lower(),
        "content": (outcome.content_description or "").lower(),
        "standard": (outcome.achievement_standard or "").lower(),
    }
    # Weighted term overlap: an exact code hit dominates, then area/strand, then body.
    weights = {"code": 8, "area": 4, "subject": 3, "strand": 3, "content": 1, "standard": 1}
    score = 0
    for tok in tokens:
        for field, text in haystacks.items():
            if tok and tok in text:
                score += weights[field]
    return score


def retrieve_outcomes(tenant_id, question, *, year_level=None, learning_area=None, limit=5):
    """Return up to `limit` most-relevant CurriculumOutcome rows for this tenant."""
    qs = CurriculumOutcome.objects.filter(tenant_id=tenant_id, is_active=True)
    if year_level is not None:
        qs = qs.filter(year_level=year_level)
    if learning_area:
        qs = qs.filter(learning_area__iexact=learning_area)

    # Direct code lookup short-circuits ranking.
    code_match = _CODE_RE.search(question or "")
    if code_match:
        exact = list(qs.filter(code__iexact=code_match.group(0)))
        if exact:
            return exact[:limit]

    tokens = _tokens(question)
    if not tokens:
        return []

    scored = [(o, _score(o, tokens)) for o in qs]
    ranked = [o for o, s in sorted(scored, key=lambda p: p[1], reverse=True) if s > 0]
    return ranked[:limit]
