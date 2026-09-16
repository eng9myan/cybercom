"""
Academic Integrity & Authenticity (capability #3).

Evaluates *process provenance* — how the work was produced — NOT the text itself.
There is deliberately no AI-text classifier: those have unacceptable false-positive
rates and are indefensible against a student. Instead we score observable process
signals (draft history, edit span, paste behaviour, disclosure) into an advisory
`risk_band` that only flags work for a human. The human always makes the decision;
the system never auto-accuses. Disclosed AI use is treated as compliance to assess
against the task's permitted-use policy, not as misconduct.
"""


def assess(evidence: dict):
    """
    Return (risk_band, signals) from process-provenance evidence.
    `evidence` keys: draft_versions, edit_span_minutes, paste_events,
    large_paste_events, disclosed_ai_use.
    """
    draft_versions = int(evidence.get("draft_versions", 0) or 0)
    edit_span = int(evidence.get("edit_span_minutes", 0) or 0)
    paste_events = int(evidence.get("paste_events", 0) or 0)
    large_pastes = int(evidence.get("large_paste_events", 0) or 0)
    disclosed = bool(evidence.get("disclosed_ai_use", False))

    score = 0
    signals = {}

    if draft_versions <= 1:
        score += 2
        signals["few_drafts"] = "Little or no draft history — genuine writing usually leaves versions."
    if edit_span < 10:
        score += 2
        signals["short_edit_span"] = f"Very short edit span ({edit_span} min) for the task."
    if large_pastes >= 1:
        score += 2
        signals["large_pastes"] = f"{large_pastes} large paste event(s) detected."
    if paste_events >= 5:
        score += 1
        signals["many_pastes"] = f"{paste_events} paste events."
    if not disclosed and (large_pastes >= 1 or draft_versions <= 1):
        score += 1
        signals["no_disclosure"] = "No AI-use disclosure alongside paste/low-draft signals."

    band = "high" if score >= 5 else "medium" if score >= 3 else "low"

    if disclosed:
        signals["ai_disclosed"] = (
            "AI use was disclosed — assess against the task's permitted-use policy, "
            "not as misconduct."
        )
        if band == "high":
            band = "medium"  # disclosure lowers misconduct concern

    signals["score"] = score
    signals["advisory_only"] = "Advisory flag only — a human makes the final decision. Never auto-accuses."
    return band, signals
