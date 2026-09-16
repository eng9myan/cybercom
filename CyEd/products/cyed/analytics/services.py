"""
Predictive student-success analytics.

Computes a real, explainable at-risk signal per student from three observable
sources — attendance, academic performance, and behaviour — so counsellors are
alerted early. Rule-based and transparent (every band lists its factors); the
model can later be swapped for a trained classifier behind the same contract.
"""

from decimal import Decimal

from products.cyed.attendance.models import AttendanceMark
from products.cyed.gradebook.models import Grade
from products.cyed.sis.models import Student
from products.cyed.wellbeing.models import BehaviourIncident


def _attendance_by_student(tenant_id):
    data = {}
    for m in AttendanceMark.objects.filter(tenant_id=tenant_id).values("student_id", "status"):
        d = data.setdefault(m["student_id"], {"total": 0, "absent": 0})
        d["total"] += 1
        if m["status"] in ("absent", "left_early"):
            d["absent"] += 1
    return data


def _grades_by_student(tenant_id):
    data = {}
    rows = (
        Grade.objects.filter(tenant_id=tenant_id, score__isnull=False)
        .select_related("assessment")
        .values("student_id", "score", "assessment__max_score")
    )
    for r in rows:
        maxs = r["assessment__max_score"] or Decimal("0")
        if not maxs:
            continue
        pct = float(r["score"]) / float(maxs) * 100
        d = data.setdefault(r["student_id"], [])
        d.append(pct)
    return {sid: (sum(v) / len(v)) for sid, v in data.items() if v}


def _major_incidents_by_student(tenant_id):
    data = {}
    for b in BehaviourIncident.objects.filter(tenant_id=tenant_id, category="major").values("student_id"):
        data[b["student_id"]] = data.get(b["student_id"], 0) + 1
    return data


def compute_at_risk(tenant_id):
    attendance = _attendance_by_student(tenant_id)
    grades = _grades_by_student(tenant_id)
    incidents = _major_incidents_by_student(tenant_id)

    results = []
    for s in Student.objects.filter(tenant_id=tenant_id):
        att = attendance.get(s.id, {"total": 0, "absent": 0})
        absence_rate = (att["absent"] / att["total"]) if att["total"] else 0.0
        avg_grade = grades.get(s.id)
        major = incidents.get(s.id, 0)

        score = 0
        factors = []
        if absence_rate > 0.30:
            score += 3
            factors.append(f"High absence rate ({absence_rate:.0%})")
        elif absence_rate > 0.15:
            score += 2
            factors.append(f"Elevated absence rate ({absence_rate:.0%})")
        if avg_grade is not None:
            if avg_grade < 50:
                score += 3
                factors.append(f"Low average grade ({avg_grade:.0f}%)")
            elif avg_grade < 65:
                score += 1
                factors.append(f"Below-benchmark grade ({avg_grade:.0f}%)")
        if major >= 2:
            score += 3
            factors.append(f"{major} major behaviour incidents")
        elif major == 1:
            score += 2
            factors.append("1 major behaviour incident")

        band = "high" if score >= 5 else "medium" if score >= 2 else "low"
        results.append({
            "student_id": str(s.id),
            "student_name": f"{s.first_name} {s.last_name}".strip(),
            "year_level": s.year_level,
            "risk_band": band,
            "score": score,
            "absence_rate": round(absence_rate, 3),
            "avg_grade": round(avg_grade, 1) if avg_grade is not None else None,
            "major_incidents": major,
            "factors": factors,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results
