"""
AI data-minimisation proxy (ST4S / APP requirement).

Strips personally identifiable information from any text before it is sent to an
external LLM: emails, phone numbers, student-ID patterns, and any explicit names
passed by the caller (e.g. the student's own name when a student_id is known).
Prompts to the model therefore carry no unnecessary identifiers.
"""

import re

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<!\w)(?:\+?61|0)[\d\s\-()]{7,}\d(?!\w)")
_STUDENT_ID = re.compile(r"\bS\d{3,}\b", re.IGNORECASE)
# Long digit runs (e.g. ID/USI numbers) — 6+ digits.
_LONG_DIGITS = re.compile(r"\b\d{6,}\b")


def anonymise(text: str, *, names: list[str] | None = None) -> str:
    if not text:
        return text
    out = text
    for name in names or []:
        name = (name or "").strip()
        if len(name) >= 2:
            out = re.sub(rf"\b{re.escape(name)}\b", "[name]", out, flags=re.IGNORECASE)
    out = _EMAIL.sub("[email]", out)
    out = _PHONE.sub("[phone]", out)
    out = _STUDENT_ID.sub("[id]", out)
    out = _LONG_DIGITS.sub("[number]", out)
    return out


def names_for_student(tenant_id, student_id) -> list[str]:
    """Return the identifier strings to scrub for a given student."""
    if not student_id:
        return []
    from products.cyed.sis.models import Student

    s = Student.objects.filter(tenant_id=tenant_id, id=student_id).first()
    if not s:
        return []
    parts = [s.first_name, s.last_name, f"{s.first_name} {s.last_name}".strip()]
    if s.student_number:
        parts.append(s.student_number)
    if s.email:
        parts.append(s.email)
    return [p for p in parts if p]
