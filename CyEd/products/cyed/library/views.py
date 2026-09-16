from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff, _email, scope_queryset_by_student
from products.cyed.library import services
from products.cyed.library.models import Book, LibraryPolicy, Loan, get_policy
from products.cyed.library.serializers import (
    BookSerializer,
    LibraryPolicySerializer,
    LoanSerializer,
)


class BookViewSet(TenantScopedModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        return [IsAuthenticatedViaClaims()] if self.action in ("list", "retrieve") else [IsStaff()]


class LibraryPolicyViewSet(TenantScopedModelViewSet):
    """
    The school's borrowing rules. One row per tenant, created on first read so
    a new school has working defaults rather than an empty page.
    """

    queryset = LibraryPolicy.objects.all()
    serializer_class = LibraryPolicySerializer
    permission_classes = [IsStaff]
    http_method_names = ["get", "put", "patch", "head", "options"]

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(get_policy(request.tenant_id)).data)


class LoanViewSet(TenantScopedModelViewSet):
    queryset = Loan.objects.select_related("book", "student").all()
    serializer_class = LoanSerializer

    def get_permissions(self):
        return [IsAuthenticatedViaClaims()] if self.action in ("list", "retrieve") else [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        return qs

    def perform_create(self, serializer):
        """
        Issue a book: check availability and the borrower's limit, then set the
        due date from policy rather than trusting whatever the client sent.
        """
        from rest_framework.exceptions import ValidationError

        book = serializer.validated_data["book"]
        student = serializer.validated_data["student"]

        if book.copies_available < 1:
            raise ValidationError({"book": "No copies available."})

        allowed, reason = services.check_can_borrow(self.request.tenant_id, student)
        if not allowed:
            raise ValidationError({"student": reason})

        borrowed_on = serializer.validated_data.get("borrowed_on")
        loan = serializer.save(
            tenant_id=self.request.tenant_id,
            due_on=services.due_date_for(self.request.tenant_id, borrowed_on),
        )
        book.copies_available -= 1
        book.save(update_fields=["copies_available", "updated_at"])
        return loan

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def return_book(self, request, pk=None):
        """Take the book back and freeze whatever fine it accrued."""
        try:
            loan = services.return_loan(self.get_object())
        except services.CirculationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(loan).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaff])
    def renew(self, request, pk=None):
        """Extend a loan. Refused once overdue."""
        try:
            loan = services.renew_loan(self.get_object())
        except services.CirculationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(loan).data)

    @action(detail=True, methods=["post"], url_path="waive-fine", permission_classes=[IsStaff])
    def waive_fine(self, request, pk=None):
        try:
            loan = services.waive_fine(
                self.get_object(), reason=request.data.get("reason", ""), actor=_email(request)
            )
        except services.CirculationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(loan).data)

    @action(detail=False, methods=["get"], permission_classes=[IsStaff])
    def overdue(self, request):
        """Outstanding overdue loans with running fines, longest overdue first."""
        return Response(services.overdue_report(request.tenant_id))

    @action(detail=False, methods=["post"], url_path="mark-overdue", permission_classes=[IsStaff])
    def mark_overdue(self, request):
        """Daily sweep: flip borrowed loans past their due date."""
        return Response({"updated": services.mark_overdue(request.tenant_id)})

    @action(detail=False, methods=["get"], permission_classes=[IsStaff])
    def fines(self, request):
        """What one borrower owes. `?student=<uuid>`."""
        student_id = request.query_params.get("student")
        if not student_id:
            return Response({"detail": "student is required."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "student": student_id,
            "outstanding": str(services.student_fines(request.tenant_id, student_id)),
        })
