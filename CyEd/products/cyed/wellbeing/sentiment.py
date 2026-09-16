"""
Lightweight lexicon sentiment for student wellbeing check-ins. Deliberately
transparent and dependency-free (no opaque model): a positive/negative word
balance plus a distress/crisis term list that always flags for human review.
This is a screening aid for pastoral staff — never an automated judgement.
"""

import re

_POSITIVE = {
    "good", "great", "happy", "excited", "fine", "ok", "okay", "calm", "confident",
    "proud", "enjoy", "enjoyed", "love", "fun", "safe", "supported", "hopeful", "better",
}
_NEGATIVE = {
    "sad", "tired", "angry", "worried", "stressed", "anxious", "nervous", "upset",
    "bad", "hard", "difficult", "lonely", "bored", "frustrated", "overwhelmed", "cry",
}
# Terms that always trigger a flag for human review regardless of balance.
_DISTRESS = {
    "bully", "bullied", "bullying", "hurt", "hurting", "alone", "hopeless", "worthless",
    "scared", "afraid", "hate", "hates", "unsafe", "panic", "can't cope", "cant cope",
    "give up", "no one", "nobody", "hopelessness", "self-harm", "harm",
}


def _tokens(text: str):
    return re.findall(r"[a-zA-Z']+", (text or "").lower())


def analyse(text: str):
    """Return (score in [-1,1], label, flagged)."""
    low = (text or "").lower()
    toks = _tokens(text)
    pos = sum(1 for t in toks if t in _POSITIVE)
    neg = sum(1 for t in toks if t in _NEGATIVE)
    distress = any(term in low for term in _DISTRESS)

    score = (pos - neg) / (pos + neg + 1)
    if distress:
        return (min(score, -0.5), "distress", True)
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    # A strongly negative check-in (no crisis word) still gets flagged.
    flagged = label == "negative" and neg >= 2
    return (round(score, 3), label, flagged)
