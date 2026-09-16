"""
Bulk data-migration import for onboarding a school (or whole group) from a
legacy SIS. Accepts CSV and upserts by natural key, returning a per-row report
so an admin can fix and re-run. Idempotent: re-importing the same file updates
rather than duplicates.
"""

import csv
import io


def _open_csv(file_bytes):
    text = file_bytes.decode("utf-8-sig")  # tolerate Excel BOM
    return csv.DictReader(io.StringIO(text))


def _int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "y")


def import_students(tenant_id, file_bytes, campus_by_code=None):
    """
    Columns (header row, case-insensitive): first_name, last_name,
    student_number, date_of_birth (YYYY-MM-DD), gender, year_level, email,
    enrolment_status, usi, state_student_number, indigenous_status,
    country_of_birth, language_at_home, lbote, campus_code.

    Upsert key: student_number (falls back to first+last+dob when blank).
    """
    from products.cyed.org.models import Campus
    from products.cyed.sis.models import Student

    if campus_by_code is None:
        campus_by_code = {c.code: c for c in Campus.objects.filter(tenant_id=tenant_id) if c.code}

    report = {"created": 0, "updated": 0, "errors": []}
    reader = _open_csv(file_bytes)
    for i, row in enumerate(reader, start=2):  # row 1 is the header
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        first = row.get("first_name")
        last = row.get("last_name")
        if not first or not last:
            report["errors"].append({"row": i, "error": "first_name and last_name are required"})
            continue

        fields = {
            "first_name": first,
            "last_name": last,
            "gender": row.get("gender", ""),
            "year_level": _int(row.get("year_level"), 7),
            "email": row.get("email", ""),
            "enrolment_status": row.get("enrolment_status") or "enrolled",
            "usi": row.get("usi", ""),
            "state_student_number": row.get("state_student_number", ""),
            "indigenous_status": row.get("indigenous_status") or "9",
            "country_of_birth": row.get("country_of_birth", ""),
            "language_at_home": row.get("language_at_home", ""),
            "lbote": _bool(row.get("lbote")),
        }
        dob = row.get("date_of_birth")
        if dob:
            fields["date_of_birth"] = dob  # ISO string; Django parses on save
        code = row.get("campus_code")
        if code:
            campus = campus_by_code.get(code)
            if campus is None:
                report["errors"].append({"row": i, "error": f"unknown campus_code '{code}'"})
                continue
            fields["campus"] = campus

        number = row.get("student_number", "")
        try:
            if number:
                obj, created = Student.objects.update_or_create(
                    tenant_id=tenant_id, student_number=number, defaults=fields)
            else:
                lookup = {"tenant_id": tenant_id, "first_name": first, "last_name": last,
                          "date_of_birth": fields.get("date_of_birth")}
                obj, created = Student.objects.update_or_create(**lookup, defaults=fields)
            report["created" if created else "updated"] += 1
        except Exception as exc:  # bad date, constraint, etc. — report, keep going
            report["errors"].append({"row": i, "error": str(exc)})
    return report


def import_staff(tenant_id, file_bytes, campus_by_code=None):
    """
    Columns: first_name, last_name, staff_number, email, phone, role,
    department, campus_code. Upsert key: staff_number (else email).
    """
    from products.cyed.hr.models import Staff
    from products.cyed.org.models import Campus

    if campus_by_code is None:
        campus_by_code = {c.code: c for c in Campus.objects.filter(tenant_id=tenant_id) if c.code}

    report = {"created": 0, "updated": 0, "errors": []}
    reader = _open_csv(file_bytes)
    valid_roles = {c[0] for c in Staff.ROLE_CHOICES}
    for i, row in enumerate(reader, start=2):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        first = row.get("first_name")
        last = row.get("last_name")
        if not first or not last:
            report["errors"].append({"row": i, "error": "first_name and last_name are required"})
            continue

        role = row.get("role", "teacher")
        fields = {
            "first_name": first,
            "last_name": last,
            "email": row.get("email", ""),
            "phone": row.get("phone", ""),
            "role": role if role in valid_roles else "teacher",
            "department": row.get("department", ""),
        }
        code = row.get("campus_code")
        if code:
            campus = campus_by_code.get(code)
            if campus is None:
                report["errors"].append({"row": i, "error": f"unknown campus_code '{code}'"})
                continue
            fields["campus"] = campus

        number = row.get("staff_number", "")
        email = row.get("email", "")
        try:
            if number:
                obj, created = Staff.objects.update_or_create(
                    tenant_id=tenant_id, staff_number=number, defaults=fields)
            elif email:
                obj, created = Staff.objects.update_or_create(
                    tenant_id=tenant_id, email=email, defaults=fields)
            else:
                Staff.objects.create(tenant_id=tenant_id, **fields)
                created = True
            report["created" if created else "updated"] += 1
        except Exception as exc:
            report["errors"].append({"row": i, "error": str(exc)})
    return report
