"""
ACARA v9 curriculum ingestion.

Loads outcome rows (from the licensed ACARA export — CSV/JSON — or the bundled
starter set) into the tenant's CurriculumOutcome registry. Idempotent: re-running
updates existing codes rather than duplicating. This is what makes the AI's
grounding real across F–10 instead of the handful of seeded demo outcomes.
"""

from products.cyed.curriculum.models import CurriculumOutcome

_YEAR_MAP = {"f": 0, "foundation": 0, "prep": 0, "k": 0}


def _year(value) -> int:
    if value is None or value == "":
        return 0
    s = str(value).strip().lower()
    if s in _YEAR_MAP:
        return 0
    digits = "".join(ch for ch in s if ch.isdigit())
    return int(digits) if digits else 0


def import_outcomes(tenant_id, rows, *, framework="ACARA v9"):
    """
    Upsert a list of outcome dicts. Each row needs at least `code` and
    `learning_area`. Returns a summary: {created, updated, skipped, errors}.
    """
    created = updated = skipped = 0
    errors = []

    for i, row in enumerate(rows):
        code = (row.get("code") or "").strip()
        learning_area = (row.get("learning_area") or "").strip()
        if not code or not learning_area:
            skipped += 1
            errors.append({"row": i, "error": "missing code or learning_area", "code": code})
            continue

        row_framework = (row.get("framework") or framework).strip()
        defaults = {
            "learning_area": learning_area,
            "subject": (row.get("subject") or "").strip(),
            "year_level": _year(row.get("year_level")),
            "strand": (row.get("strand") or "").strip(),
            "sub_strand": (row.get("sub_strand") or "").strip(),
            "content_description": (row.get("content_description") or "").strip(),
            "achievement_standard": (row.get("achievement_standard") or "").strip(),
            "elaboration": (row.get("elaboration") or "").strip(),
            "state": (row.get("state") or "").strip(),
            "is_active": True,
        }
        obj, was_created = CurriculumOutcome.objects.update_or_create(
            tenant_id=tenant_id, code=code, framework=row_framework, defaults=defaults
        )
        created += int(was_created)
        updated += int(not was_created)

    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors}
