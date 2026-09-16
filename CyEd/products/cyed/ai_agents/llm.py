"""
LLM generation for the CyEd agents — a real, env-gated Anthropic client.

Enabled only when BOTH `CYED_LLM_ENABLED=1` and `CYED_ANTHROPIC_API_KEY` are
set; otherwise `generate()` returns None and callers fall back to a grounded,
extractive answer. Any network/parse error also returns None (fail-safe): the
tutor/teacher-tools stay usable and grounded even if the model is unreachable.

Grounding is enforced in the system prompt: the model may answer ONLY from the
supplied ACARA context and must cite codes. Student input is never used for
training (Anthropic API is not a training channel); AU data-residency and any
retention controls are handled at deployment/config.
"""

import json
import os
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5"
MAX_TOKENS = 900

SYSTEM_PROMPT = (
    "You are a curriculum-aligned assistant for Australian schools. "
    "Answer ONLY using the provided Australian Curriculum (ACARA) context. "
    "If the context does not cover the question, reply that you can only help "
    "with topics in the curriculum. Always cite the relevant ACARA code(s). "
    "Keep language age-appropriate. Do not invent facts beyond the context."
)


def is_enabled() -> bool:
    return os.environ.get("CYED_LLM_ENABLED") == "1"


def _api_key() -> str:
    return os.environ.get("CYED_ANTHROPIC_API_KEY", "")


def _post(payload: dict, api_key: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed host)
        return json.loads(resp.read().decode("utf-8"))


SOCRATIC_SYSTEM_PROMPT = (
    "You are a Socratic tutor for an Australian school student. Using ONLY the "
    "provided Australian Curriculum (ACARA) context, guide the student with "
    "open-ended questions and small hints. NEVER give the final answer, the "
    "numerical solution, or a complete worked solution. Ask one step at a time, "
    "check understanding, and reference the relevant ACARA code. If the question "
    "is outside the curriculum context, say you can only help with their "
    "curriculum. Keep it encouraging and age-appropriate."
)


def generate(*, question: str, context: str, model_name: str | None = None, system: str | None = None) -> str | None:
    """
    Return a model answer grounded in `context`, or None when the LLM is not
    configured or the call fails (caller then uses the extractive fallback).
    Pass `system` to override the default (e.g. the Socratic prompt).
    """
    if not is_enabled():
        return None
    api_key = _api_key()
    if not api_key:
        return None

    payload = {
        "model": model_name or DEFAULT_MODEL,
        "max_tokens": MAX_TOKENS,
        "system": system or SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": f"ACARA curriculum context:\n{context}\n\nQuestion: {question}",
            }
        ],
    }
    try:
        data = _post(payload, api_key)
    except Exception:
        return None  # fail-safe → grounded extractive fallback

    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()
    return text or None
