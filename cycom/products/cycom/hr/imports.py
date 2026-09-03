"""
Employee bulk-import engine.

Two modes on the same validated row set:
  * dry_run=True  -> validate only, return per-row status (no writes)
  * dry_run=False -> create valid rows, skip invalid ones (partial accept)

Accepts the loose field names the import wizard sends (employee_no, name,
role, ...) and maps them onto the Employee model. Validation catches missing
required fields, bad email, and duplicate employee numbers (both within the
file and against existing rows for the tenant).
"""

from __future__ import annotations

import re
from datetime import date

from django.db import transaction

from products.cycom.hr.models import Employee

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _split_name(full: str) -> tuple[str, str]:
    parts = (full or "").strip().split()
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def _clean(row: dict) -> dict:
    """Normalize a loose wizard row into Employee-shaped fields."""
    first, last = _split_name(row.get("name", ""))
    hire = (row.get("hire_date") or "").strip() or str(date.today())
    return {
        "employee_number": (row.get("employee_no") or row.get("employee_number") or "").strip(),
        "first_name": first,
        "last_name": last,
        "email": (row.get("email") or "").strip(),
        "phone": (row.get("phone") or "").strip(),
        "job_title": (row.get("role") or row.get("job_title") or "").strip(),
        "department": (row.get("department") or "").strip(),
        "hire_date": hire,
    }


def validate_rows(rows: list[dict], tenant_id) -> list[dict]:
    """Return [{row, index, valid, errors, data}] for every input row."""
    existing = set(
        Employee.objects.filter(tenant_id=tenant_id).values_list("employee_number", flat=True)
    )
    seen: set[str] = set()
    results = []
    for i, raw in enumerate(rows):
        data = _clean(raw)
        errors = []
        num = data["employee_number"]
        if not num:
            errors.append("Missing employee code.")
        if not data["first_name"]:
            errors.append("Missing name.")
        if data["email"] and not _EMAIL_RE.match(data["email"]):
            errors.append(f"Invalid email '{data['email']}'.")
        if num and num in existing:
            errors.append(f"Employee code '{num}' already exists.")
        if num and num in seen:
            errors.append(f"Duplicate employee code '{num}' within the file.")
        if num:
            seen.add(num)
        results.append({"index": i, "valid": not errors, "errors": errors, "data": data})
    return results


def run_import(rows: list[dict], tenant_id, dry_run: bool = False) -> dict:
    validated = validate_rows(rows, tenant_id)
    valid = [r for r in validated if r["valid"]]
    invalid = [r for r in validated if not r["valid"]]

    imported_count = 0
    if not dry_run and valid:
        with transaction.atomic():
            Employee.objects.bulk_create(
                [Employee(tenant_id=tenant_id, **r["data"]) for r in valid]
            )
        imported_count = len(valid)

    return {
        "success": True,
        "dry_run": dry_run,
        "total": len(validated),
        "valid_count": len(valid),
        "invalid_count": len(invalid),
        "imported_count": imported_count,
        "errors": [
            {"row": r["index"] + 1, "employee_no": r["data"]["employee_number"], "errors": r["errors"]}
            for r in invalid
        ],
    }
