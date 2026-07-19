from django.utils import timezone

from products.cycom.accounting.services import post_journal_entry
from products.cycom.expenses.models import Expense


class ExpenseStateError(Exception):
    pass


def approve_and_post_expense(expense: Expense, *, approved_by: str) -> Expense:
    if expense.status != "submitted":
        raise ExpenseStateError(f"Expense must be 'submitted' to approve, is '{expense.status}'")

    entry = post_journal_entry(
        tenant_id=expense.tenant_id,
        date=expense.expense_date,
        reference=f"EXP-{expense.id}",
        currency=expense.currency,
        narration=f"Expense: {expense.employee_name} — {expense.category}",
        created_by=approved_by,
        lines=[
            {"account": expense.expense_account, "debit": expense.amount, "credit": 0},
            {"account": expense.payable_account, "debit": 0, "credit": expense.amount},
        ],
    )
    expense.status = "posted"
    expense.approved_by = approved_by
    expense.journal_entry = entry
    expense.save(update_fields=["status", "approved_by", "journal_entry", "updated_at"])
    return expense


def reject_expense(expense: Expense, *, reason: str) -> Expense:
    if expense.status != "submitted":
        raise ExpenseStateError(f"Expense must be 'submitted' to reject, is '{expense.status}'")
    expense.status = "rejected"
    expense.rejection_reason = reason
    expense.save(update_fields=["status", "rejection_reason", "updated_at"])
    return expense
