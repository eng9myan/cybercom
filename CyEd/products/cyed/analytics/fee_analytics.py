"""
Predictive fee & cash-flow analytics.

Transparent, rule-based forecast from installment history: each student gets a
payment-behaviour risk band (from overdue / partial history), and the school
gets a cash-flow forecast (upcoming dues bucketed 30/60/90 days, weighted by a
per-risk collection probability). Swappable for a trained model behind the same
shape.
"""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

COLLECTION_PROB = {"low": Decimal("0.92"), "medium": Decimal("0.65"), "high": Decimal("0.35")}


def _q(x):
    return Decimal(x).quantize(Decimal("0.01"))


def _risk_for(installments):
    overdue = sum(1 for i in installments if i.status == "overdue")
    partial = sum(1 for i in installments if i.status == "partial")
    if overdue >= 1:
        band, factors = "high", [f"{overdue} overdue installment(s)"]
    elif partial >= 1:
        band, factors = "medium", [f"{partial} partially-paid installment(s)"]
    else:
        band, factors = "low", ["payments on track"]
    return band, factors


def compute_fee_risk(tenant_id, today=None):
    from products.cyed.billing.models import Installment, StudentBill

    today = today or timezone.now().date()
    bills = (StudentBill.objects.filter(tenant_id=tenant_id, status__in=["active", "draft"])
             .select_related("student").prefetch_related("installments__payments"))

    students = []
    buckets = {"due_30": Decimal("0"), "due_60": Decimal("0"), "due_90": Decimal("0")}
    expected = {"exp_30": Decimal("0"), "exp_60": Decimal("0"), "exp_90": Decimal("0")}

    for bill in bills:
        insts = list(bill.installments.all())
        band, factors = _risk_for(insts)
        prob = COLLECTION_PROB[band]
        outstanding = sum((i.balance for i in insts if i.status != "paid"), Decimal("0"))
        predicted = _q(outstanding * prob)
        students.append({
            "student": str(bill.student_id),
            "name": f"{bill.student.first_name} {bill.student.last_name}".strip(),
            "risk_band": band,
            "factors": factors,
            "outstanding": str(_q(outstanding)),
            "predicted_collection": str(predicted),
        })
        # Cash-flow buckets by due date.
        for i in insts:
            if i.status == "paid" or not i.due_date:
                continue
            bal = i.balance
            days = (i.due_date - today).days
            if days <= 30:
                buckets["due_30"] += bal
                expected["exp_30"] += bal * prob
            elif days <= 60:
                buckets["due_60"] += bal
                expected["exp_60"] += bal * prob
            elif days <= 90:
                buckets["due_90"] += bal
                expected["exp_90"] += bal * prob

    summary = {
        "high": sum(1 for s in students if s["risk_band"] == "high"),
        "medium": sum(1 for s in students if s["risk_band"] == "medium"),
        "low": sum(1 for s in students if s["risk_band"] == "low"),
    }
    cashflow = {
        "due_30": str(_q(buckets["due_30"])), "expected_30": str(_q(expected["exp_30"])),
        "due_60": str(_q(buckets["due_60"])), "expected_60": str(_q(expected["exp_60"])),
        "due_90": str(_q(buckets["due_90"])), "expected_90": str(_q(expected["exp_90"])),
    }
    students.sort(key=lambda s: {"high": 0, "medium": 1, "low": 2}[s["risk_band"]])
    return {"summary": summary, "cashflow": cashflow, "students": students}
