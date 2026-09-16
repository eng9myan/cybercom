from decimal import Decimal

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.billing import collections, family_accounts, services
from products.cyed.billing.models import (
    BillLineItem,
    CreditNote,
    DunningCase,
    FeePlan,
    Installment,
    InstallmentPayment,
    SiblingDiscountRule,
    StudentBill,
)
from products.cyed.billing.serializers import (
    BillLineItemSerializer,
    CreditNoteSerializer,
    DunningActionSerializer,
    DunningCaseSerializer,
    FeePlanSerializer,
    InstallmentPaymentSerializer,
    InstallmentSerializer,
    SiblingDiscountRuleSerializer,
    StudentBillSerializer,
)
from products.cyed.governance.access import (
    CampusScopedMixin,
    IsFinanceOrLeadership,
    IsStaffOrParent,
    _email,
    scope_queryset_by_student,
    visible_student_ids,
)
from products.cyed.sis.models import Family


def _actor(request) -> str:
    """Who is taking a financial action — stamped onto credit notes and dunning."""
    return _email(request) or ""


class FeePlanViewSet(TenantScopedModelViewSet):
    queryset = FeePlan.objects.all()
    serializer_class = FeePlanSerializer
    permission_classes = [IsFinanceOrLeadership]


class BillLineItemViewSet(TenantScopedModelViewSet):
    queryset = BillLineItem.objects.select_related("bill").all()
    serializer_class = BillLineItemSerializer
    permission_classes = [IsFinanceOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        bill = self.request.query_params.get("bill")
        if bill:
            qs = qs.filter(bill_id=bill)
        return qs

    def perform_create(self, serializer):
        item = serializer.save(tenant_id=self.request.tenant_id)
        services.recalculate(item.bill)


class StudentBillViewSet(CampusScopedMixin, TenantScopedModelViewSet):
    """
    What a household is billed for one child.

    Staff and the child's own parents; not the child — see the note on
    `FamilyAccountViewSet`. Fee arrears are a matter between the school and the
    people paying.
    """

    queryset = StudentBill.objects.select_related("student", "plan", "academic_year") \
        .prefetch_related("line_items", "installments__payments").all()
    serializer_class = StudentBillSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffOrParent()]
        return [IsFinanceOrLeadership()]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        """Build the installment schedule from the bill's plan."""
        bill = self.get_object()
        services.resync_transport_line(bill.tenant_id, bill.student_id)
        services.generate_installments(bill)
        return Response(self.get_serializer(bill).data)

    @action(detail=True, methods=["post"])
    def recalculate(self, request, pk=None):
        bill = self.get_object()
        services.resync_transport_line(bill.tenant_id, bill.student_id)
        services.recalculate(bill)
        return Response(self.get_serializer(bill).data)

    @action(detail=False, methods=["post"])
    def run_billing(self, request):
        """Cron-style pass: mark overdue, apply late fees, send 7-day reminders."""
        tenant = request.tenant_id
        overdue = services.mark_overdue(tenant)
        late = services.apply_late_fees(tenant)
        reminders = services.send_due_reminders(tenant, within_days=int(request.data.get("within_days", 7)))
        return Response({"overdue": overdue, "late_fees_applied": late, "reminders_sent": reminders})


class InstallmentViewSet(TenantScopedModelViewSet):
    queryset = Installment.objects.select_related("bill__student").prefetch_related("payments").all()
    serializer_class = InstallmentSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffOrParent()]
        return [IsFinanceOrLeadership()]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="bill__student_id")
        bill = self.request.query_params.get("bill")
        if bill:
            qs = qs.filter(bill_id=bill)
        return qs

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        inst = self.get_object()
        amount = request.data.get("amount")
        if amount in (None, ""):
            return Response({"detail": "amount is required."}, status=status.HTTP_400_BAD_REQUEST)
        services.record_payment(
            inst, amount=amount, method=request.data.get("method", "card"),
            reference=request.data.get("reference", ""),
        )
        return Response(self.get_serializer(inst).data)


class InstallmentPaymentViewSet(TenantScopedModelViewSet):
    queryset = InstallmentPayment.objects.select_related("installment").all()
    serializer_class = InstallmentPaymentSerializer
    permission_classes = [IsFinanceOrLeadership]
    http_method_names = ["get", "head", "options"]


class CreditNoteViewSet(TenantScopedModelViewSet):
    """
    Reductions of what a family owes — distinct from refunds, which move money.

    Notes are created as drafts and become documents when issued; an issued
    note is immutable and can only be reversed by an explicit cancellation
    carrying a reason.
    """

    queryset = CreditNote.objects.select_related("student", "bill", "installment").all()
    serializer_class = CreditNoteSerializer
    permission_classes = [IsFinanceOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("bill"):
            qs = qs.filter(bill_id=params["bill"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        return qs

    def update(self, request, *args, **kwargs):
        return self._guard_frozen(super().update, request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self._guard_frozen(super().partial_update, request, *args, **kwargs)

    def _guard_frozen(self, handler, request, *args, **kwargs):
        """An issued note is a document; only a draft is still editable."""
        if self.get_object().status != "draft":
            return Response(
                {"detail": "An issued credit note cannot be edited. Cancel it and issue another."},
                status=status.HTTP_409_CONFLICT,
            )
        return handler(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if self.get_object().status != "draft":
            return Response(
                {"detail": "An issued credit note cannot be deleted. Cancel it instead."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        """Apply the reduction, post it to the ledger, and freeze the document."""
        try:
            note = collections.issue_credit_note(
                self.get_object(), actor=_actor(request)
            )
        except collections.CollectionsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(note).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Reverse an issued note. Requires a reason."""
        try:
            note = collections.cancel_credit_note(
                self.get_object(),
                reason=request.data.get("reason", ""),
                actor=_actor(request),
            )
        except collections.CollectionsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(note).data)


class DunningCaseViewSet(TenantScopedModelViewSet):
    """
    The defaulter escalation ladder: reminder → formal notice → meeting →
    referral, with a mandatory wait between rungs.
    """

    queryset = DunningCase.objects.select_related("family").prefetch_related("actions").all()
    serializer_class = DunningCaseSerializer
    permission_classes = [IsFinanceOrLeadership]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("stage"):
            qs = qs.filter(stage=params["stage"])
        if params.get("family"):
            qs = qs.filter(family_id=params["family"])
        return qs

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Open cases through /dunning-cases/sweep/ so balances are checked."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["post"])
    def sweep(self, request):
        """
        Daily job: open cases for newly overdue households and close the ones
        that have paid.
        """
        opened = collections.open_cases(request.tenant_id)
        closed = collections.auto_resolve_settled(request.tenant_id)
        return Response({"opened": len(opened), "resolved": len(closed)})

    @action(detail=True, methods=["post"])
    def escalate(self, request, pk=None):
        """Climb one rung and notify the household."""
        try:
            action_row = collections.escalate(
                self.get_object(),
                actor=_actor(request),
                note=request.data.get("note", ""),
                notify=bool(request.data.get("notify", True)),
            )
        except collections.CollectionsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(DunningActionSerializer(action_row).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Stop the letters while a conversation is happening."""
        try:
            case = collections.pause(
                self.get_object(),
                until=request.data.get("until") or None,
                reason=request.data.get("reason", ""),
                actor=_actor(request),
            )
        except collections.CollectionsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(case).data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        try:
            case = collections.resume(self.get_object())
        except collections.CollectionsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(case).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Close the case — paid, or deliberately written off."""
        try:
            case = collections.resolve(
                self.get_object(),
                note=request.data.get("note", ""),
                actor=_actor(request),
                written_off=bool(request.data.get("written_off")),
            )
        except collections.CollectionsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(case).data)


class SiblingDiscountRuleViewSet(TenantScopedModelViewSet):
    """
    The school's sibling fee structure. Finance/leadership only — these rules
    set prices for every family at once.
    """

    queryset = SiblingDiscountRule.objects.select_related("academic_year", "campus").all()
    serializer_class = SiblingDiscountRuleSerializer
    permission_classes = [IsFinanceOrLeadership]

    @action(detail=False, methods=["post"], url_path="apply-all")
    def apply_all(self, request):
        """
        Push the current rules onto every household's live bills.

        Run this after changing the fee structure: rules are evaluated when a
        schedule is built or reprorated, so existing bills keep their old
        numbers until something touches them. Without this endpoint a school
        would have to open every family to roll out a new discount.
        """
        families = Family.objects.filter(tenant_id=request.tenant_id, is_active=True)
        families_touched = bills_touched = 0
        for family in families:
            n = family_accounts.resync_family(family)
            if n:
                families_touched += 1
                bills_touched += n
        return Response({"families_updated": families_touched, "bills_updated": bills_touched})


class FamilyAccountViewSet(TenantScopedModelViewSet):
    """
    The money view of a household: one statement covering every child, across
    both the installment ledger and ad-hoc invoices.

    Readable by the family's own parents (scoped to households containing a
    child they can see) as well as finance; writable by nobody — this is a
    projection, and the underlying bills are edited where they live.

    **Students are excluded, deliberately.** Scoping alone would let one in —
    a student can see themselves, so their household matches — and they would
    read the family's outstanding balance and the billing contact's email.
    Whether the fees are behind is a conversation between the school and the
    parents, and a child finding out through a portal is not that conversation.
    """

    queryset = Family.objects.select_related("billing_contact").prefetch_related("students").all()
    serializer_class = SiblingDiscountRuleSerializer  # unused; every route below is custom
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("statement", "retrieve", "list"):
            return [IsStaffOrParent()]
        return [IsFinanceOrLeadership()]

    def get_queryset(self):
        qs = super().get_queryset()
        visible = visible_student_ids(self.request, self.request.tenant_id)
        if visible is not None:
            # A parent may read the household(s) their own children belong to,
            # and no others. Distinct because a household with two visible
            # children would otherwise appear twice.
            qs = qs.filter(students__id__in=visible).distinct()
        return qs

    def list(self, request, *args, **kwargs):
        """
        Households with an outstanding balance, largest first — the finance
        office's dunning worklist.

        `?all=1` includes families that owe nothing.
        """
        include_settled = request.query_params.get("all") == "1"
        families = list(self.get_queryset())
        # Balances in a handful of queries rather than a full statement per
        # household — the worklist is the one screen that touches every family
        # at once, so building statements here is what makes it unusable at a
        # real school's size.
        totals = family_accounts.family_totals_bulk(
            request.tenant_id, family_ids=[f.id for f in families]
        )

        rows = []
        for family in families:
            amounts = totals.get(
                str(family.id), {"balance": Decimal("0"), "overdue": Decimal("0")}
            )
            if not include_settled and amounts["balance"] <= 0:
                continue
            rows.append({
                "family": str(family.id),
                "name": family.name,
                "billing_email": family.billing_email(),
                "children_enrolled": family.students_enrolled().count(),
                "balance": str(amounts["balance"]),
                "overdue": str(amounts["overdue"]),
            })
        rows.sort(key=lambda r: Decimal(r["balance"]), reverse=True)
        return Response({"count": len(rows), "results": rows})

    def retrieve(self, request, pk=None):
        return Response(family_accounts.family_statement(self.get_object()))

    @action(detail=True, methods=["get"])
    def statement(self, request, pk=None):
        """The consolidated statement a parent receives."""
        return Response(family_accounts.family_statement(self.get_object()))

    @action(detail=True, methods=["post"])
    def resync(self, request, pk=None):
        """
        Recompute this household's bills after its membership changed.

        A child's ordinal depends on their siblings, so enrolling a younger
        child or withdrawing the eldest changes what someone *else* pays.
        """
        family = self.get_object()
        touched = family_accounts.resync_family(family)
        return Response({"bills_updated": touched, "statement": family_accounts.family_statement(family)})
