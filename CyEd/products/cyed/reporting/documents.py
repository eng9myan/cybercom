"""
Report-card document generation: freeze a snapshot at publish time, hash it for
tamper-evidence, and render an immutable, branded PDF (school name + logo, a
proper bordered grades table). Re-publishing creates a new version; old versions
are retained.
"""

import hashlib
import json


def build_snapshot(report_card) -> dict:
    student = report_card.student
    entries = [
        {
            "subject": e.subject,
            "achievement": e.achievement,
            "effort": e.effort,
            "comment": e.comment,
            "teacher_name": e.teacher_name,
        }
        for e in report_card.entries.all().order_by("subject")
    ]
    snapshot = {
        "student": {
            "id": str(student.id),
            "name": f"{student.first_name} {student.last_name}".strip(),
            "year_level": student.year_level,
            "student_number": student.student_number,
        },
        "academic_year": report_card.academic_year.name if report_card.academic_year else "",
        "term": report_card.term,
        "general_comment": report_card.general_comment,
        "entries": entries,
    }
    # Freeze the school identity onto the record too (branding at time of issue).
    try:
        from products.cyed.school.models import get_profile

        p = get_profile(report_card.tenant_id)
        snapshot["school"] = {"name": p.name, "principal_name": p.principal_name,
                              "suburb": p.suburb, "state": p.state, "design": p.report_design()}
    except Exception:
        snapshot["school"] = {"name": "School"}
    return snapshot


def _hex_rgb(h: str, default=(0.055, 0.647, 0.643)):
    try:
        h = (h or "").lstrip("#")
        return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)
    except Exception:
        return default


def content_hash(snapshot: dict) -> str:
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_ACH = {"A": "A — Excellent", "B": "B — Good", "C": "C — Satisfactory",
        "D": "D — Limited", "E": "E — Very Low", "": "—"}
_EFF = {"high": "High", "consistent": "Consistent", "developing": "Developing", "low": "Low", "": "—"}


def render_report_pdf(snapshot: dict, chash: str, version: int, *, logo_jpeg: bytes | None = None) -> bytes:
    from products.cyed.reporting.pdf import PdfCanvas, wrap

    c = PdfCanvas()
    W, H = c.w, c.h
    left, right = 40, W - 40
    school = snapshot.get("school") or {}
    design = school.get("design") or {}
    accent = _hex_rgb(design.get("accent_color"))
    accent_tint = tuple(min(1.0, v + (1 - v) * 0.82) for v in accent)  # light header fill
    show_effort = design.get("show_effort", True)
    show_general = design.get("show_general_comment", True)
    s = snapshot["student"]

    # ── Header: logo + school name ──────────────────────────────────────────
    text_x = left
    if logo_jpeg and design.get("show_logo", True):
        from products.cyed.reporting.pdf import jpeg_info
        if jpeg_info(logo_jpeg):
            c.image("Logo", left, H - 90, 55, 55, logo_jpeg)
            text_x = left + 68
    c.text(text_x, H - 55, school.get("name", "School"), size=20, bold=True)
    sub = design.get("title") or "Student Report Card"
    loc = " · ".join(x for x in [school.get("suburb"), school.get("state")] if x)
    c.text(text_x, H - 74, sub + (f"   ({loc})" if loc else ""), size=11)
    c.rect(left, H - 100, right - left, 3, fill=accent, stroke=False)  # accent rule

    # ── Student block ───────────────────────────────────────────────────────
    y = H - 120
    c.text(left, y, "Student:", size=10, bold=True)
    c.text(left + 55, y, s["name"], size=10)
    c.text(left + 300, y, "Year:", size=10, bold=True)
    c.text(left + 335, y, f"F" if s["year_level"] == 0 else str(s["year_level"]), size=10)
    y -= 16
    c.text(left, y, "Student No:", size=10, bold=True)
    c.text(left + 65, y, s["student_number"] or "—", size=10)
    c.text(left + 300, y, "Year/Term:", size=10, bold=True)
    c.text(left + 360, y, f"{snapshot['academic_year']} · {snapshot['term']}", size=10)

    # ── Grades table (columns depend on the school's design) ────────────────
    if show_effort:
        cols = [left, left + 150, left + 275, left + 355, right]
        headers = ["Subject", "Achievement", "Effort", "Comment"]
        comment_col = 3
    else:
        cols = [left, left + 170, left + 300, right]
        headers = ["Subject", "Achievement", "Comment"]
        comment_col = 2
    comment_chars = 50 if not show_effort else 34
    top = y - 24
    header_h = 20
    c.rect(left, top - header_h, right - left, header_h, fill=accent_tint)
    for i, htext in enumerate(headers):
        c.text(cols[i] + 5, top - header_h + 6, htext, size=9, bold=True)
    for x in cols[1:-1]:
        c.line(x, top - header_h, x, top, 0.7)

    row_y = top - header_h
    for e in snapshot["entries"]:
        comment_lines = wrap(e["comment"], comment_chars, max_lines=2)
        row_h = max(20, 6 + 12 * len(comment_lines))
        row_y -= row_h
        c.rect(left, row_y, right - left, row_h)
        for x in cols[1:-1]:
            c.line(x, row_y, x, row_y + row_h, 0.7)
        cy = row_y + row_h - 13
        c.text(cols[0] + 5, cy, (e["subject"] or "")[:26], size=9)
        c.text(cols[1] + 5, cy, _ACH.get(e["achievement"], e["achievement"] or "—"), size=9)
        if show_effort:
            c.text(cols[2] + 5, cy, _EFF.get(e["effort"], e["effort"] or "—"), size=9)
        for j, cl in enumerate(comment_lines):
            c.text(cols[comment_col] + 5, cy - j * 12, cl, size=8)

    # ── General comment ─────────────────────────────────────────────────────
    gy = row_y - 26
    if show_general and snapshot.get("general_comment"):
        c.text(left, gy, "General comment", size=10, bold=True)
        gy -= 14
        for line in wrap(snapshot["general_comment"], 95, max_lines=4):
            c.text(left, gy, line, size=9)
            gy -= 12

    # ── Footer: signature + tamper-evidence ─────────────────────────────────
    fy = 92
    c.rect(left, fy + 22, right - left, 2, fill=accent, stroke=False)
    if design.get("footer"):
        c.text(left, fy + 8, design["footer"][:110], size=8)
    if school.get("principal_name"):
        c.text(left, fy - 6, f"Principal: {school['principal_name']}", size=9)
    c.text(left, fy - 20, f"Published document version {version}", size=8)
    c.text(left, fy - 32, f"Tamper-evident SHA-256: {chash}", size=7)
    c.text(left, fy - 44, "Official published record. Any alteration changes the hash above.", size=8)
    return c.build()
