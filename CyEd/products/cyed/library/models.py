from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class LibraryPolicy(BaseModel):
    """
    One school's borrowing rules: how many books, for how long, and what an
    overdue day costs.

    A singleton per tenant. Kept as data rather than constants because the
    limits are exactly what differs between a primary and a secondary campus,
    and hard-coding them means the librarian has to raise a ticket to change a
    loan period.
    """

    max_loans_per_student = models.PositiveSmallIntegerField(default=3)
    loan_days = models.PositiveSmallIntegerField(default=14)
    fine_per_day = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.20"))
    # A fine that can grow without limit turns a lost library book into a debt
    # larger than the book. Capped at the replacement value by default.
    max_fine_per_loan = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("20.00"))
    # Days after the due date before a fine starts accruing. Schools routinely
    # allow a few days so a weekend or a sick day does not become a debt.
    grace_days = models.PositiveSmallIntegerField(default=2)
    # Blocking a child from borrowing over a small debt keeps them out of the
    # library, which is the opposite of the point. Off by default.
    block_borrowing_when_fined = models.BooleanField(default=False)
    fine_block_threshold = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("10.00"))

    class Meta:
        db_table = "cyed_library_policies"
        constraints = [
            models.UniqueConstraint(fields=["tenant_id"], name="uniq_library_policy_per_tenant"),
        ]

    def __str__(self):
        return f"Library policy ({self.max_loans_per_student} loans / {self.loan_days} days)"


def get_policy(tenant_id) -> "LibraryPolicy":
    policy, _ = LibraryPolicy.objects.get_or_create(tenant_id=tenant_id)
    return policy


class Book(BaseModel):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=100, blank=True)
    copies_total = models.PositiveSmallIntegerField(default=1)
    copies_available = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "cyed_library_books"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Loan(BaseModel):
    STATUS = [("borrowed", "Borrowed"), ("returned", "Returned"), ("overdue", "Overdue")]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="loans")
    student = models.ForeignKey("cyed_sis.Student", on_delete=models.CASCADE, related_name="loans")
    borrowed_on = models.DateField(default=timezone.localdate)
    due_on = models.DateField(null=True, blank=True)
    returned_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="borrowed")
    # Frozen when the book comes back. Kept on the loan rather than recomputed
    # on read so that changing the policy later cannot silently rewrite a fine
    # a family has already been told about — or already paid.
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fine_waived = models.BooleanField(default=False)
    fine_waived_by = models.CharField(max_length=255, blank=True)
    fine_waive_reason = models.CharField(max_length=255, blank=True)
    fine_paid_on = models.DateField(null=True, blank=True)
    renewed_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cyed_library_loans"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "status", "due_on"], name="idx_loan_status_due"),
        ]

    def days_overdue(self, as_at=None) -> int:
        """Days past due, ignoring the grace period (that is applied to the fine)."""
        if self.due_on is None:
            return 0
        end = self.returned_on or (as_at or timezone.localdate())
        return max(0, (end - self.due_on).days)

    def accrued_fine(self, policy, as_at=None) -> Decimal:
        """
        What this loan owes right now.

        Live for an outstanding loan, frozen once returned — a returned book's
        fine stops growing, which is the difference between a fine and a
        punishment.
        """
        if self.fine_waived:
            return Decimal("0")
        if self.status == "returned":
            return Decimal(self.fine_amount)
        chargeable = max(0, self.days_overdue(as_at) - policy.grace_days)
        fine = Decimal(policy.fine_per_day) * chargeable
        return min(fine, Decimal(policy.max_fine_per_loan))

    def outstanding_fine(self, policy, as_at=None) -> Decimal:
        if self.fine_waived or self.fine_paid_on:
            return Decimal("0")
        return self.accrued_fine(policy, as_at)

    def __str__(self):
        return f"{self.book_id} → {self.student_id} ({self.status})"
