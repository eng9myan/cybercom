"""
Meeting summariser — real deterministic extraction of a summary, action items,
and key points from a transcript. Upgrades to the LLM (ai_agents.llm) when
enabled, behind the same return shape.
"""

import re

_ACTION_CUES = re.compile(
    r"\b(will|need to|needs to|to do|follow up|action|should|by (?:next |the )?\w+|agree(?:d)? to|"
    r"send|schedule|book|arrange|provide|contact)\b",
    re.IGNORECASE,
)


def _sentences(text: str):
    parts = re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip())
    return [p.strip() for p in parts if len(p.strip()) > 3]


def summarise(transcript: str) -> dict:
    sents = _sentences(transcript)
    if not sents:
        return {"summary": "", "action_items": [], "key_points": []}

    action_items = [s for s in sents if _ACTION_CUES.search(s)][:8]
    # Key points = the longest/most-informative non-action sentences.
    non_action = [s for s in sents if s not in action_items]
    key_points = sorted(non_action, key=len, reverse=True)[:5]

    summary = (
        f"Meeting covered {len(sents)} points across {len(set(w.lower() for s in sents for w in s.split()[:1]))} "
        f"topics. {len(action_items)} action item(s) identified. "
        + (key_points[0] if key_points else "")
    )
    return {"summary": summary.strip(), "action_items": action_items, "key_points": key_points}


def summarise_with_llm(transcript: str, model_name="claude-sonnet-5") -> dict:
    """Optional richer summary via the LLM seam; falls back to the deterministic one."""
    from products.cyed.ai_agents import llm

    out = llm.generate(
        question="Summarise this meeting: give a short summary, action items, and key points.",
        context=transcript, model_name=model_name,
    )
    base = summarise(transcript)
    if out:
        base["summary"] = out
    return base
