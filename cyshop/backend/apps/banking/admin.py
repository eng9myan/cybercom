from django.contrib import admin

from .models import (
    BankAccount, BankStatement, BankStatementLine, ReconciliationSession,
)


class _RO(admin.ModelAdmin):
    def has_add_permission(self, r): return False
    def has_change_permission(self, r, o=None): return False
    def has_delete_permission(self, r, o=None): return False


@admin.register(BankAccount)
class BankAccountAdmin(_RO):
    list_display = ("name", "bank_name", "currency", "opening_balance", "book_balance", "is_active")


@admin.register(BankStatement)
class BankStatementAdmin(_RO):
    list_display = ("bank_account", "reference", "statement_date", "line_count", "closing_balance")


@admin.register(BankStatementLine)
class BankStatementLineAdmin(_RO):
    list_display = ("bank_account", "txn_date", "description", "amount", "matched", "reconciled", "match_type")
    list_filter = ("matched", "reconciled", "match_type")


@admin.register(ReconciliationSession)
class ReconciliationSessionAdmin(_RO):
    list_display = ("bank_account", "period_start", "period_end", "statement_closing_balance",
                    "book_balance", "difference", "status")
    list_filter = ("status",)
