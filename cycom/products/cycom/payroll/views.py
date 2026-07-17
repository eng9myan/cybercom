from decimal import Decimal

from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.accounting.services import UnbalancedEntryError, post_journal_entry
from products.cycom.hr.models import Contract
from products.cycom.payroll.models import AttendanceRecord, PayrollRun, Payslip
from products.cycom.payroll.serializers import (
    AttendanceRecordSerializer,
    PayrollRunSerializer,
    PayslipSerializer,
)
from products.cycom.payroll.services import compute_payslip


class AttendanceRecordViewSet(TenantScopedModelViewSet):
    queryset = AttendanceRecord.objects.select_related("employee").all()
    serializer_class = AttendanceRecordSerializer

    @action(detail=False, methods=["post"], url_path="import")
    def import_records(self, request):
        """
        Generic biometric-device import: accepts a list of punches in the
        shape any device export can be mapped to
        [{employee, date, check_in, check_out}], tagged source=biometric_import.
        Not a vendor-specific driver — the integration point is this endpoint.
        """
        records = request.data if isinstance(request.data, list) else request.data.get("records", [])
        if not records:
            raise ValidationError("No records provided.")
        created = []
        for row in records:
            ser = AttendanceRecordSerializer(data={**row, "source": "biometric_import"})
            ser.is_valid(raise_exception=True)
            obj = AttendanceRecord.objects.update_or_create(
                tenant_id=self.request.tenant_id,
                employee_id=ser.validated_data["employee"].id,
                date=ser.validated_data["date"],
                defaults={
                    "check_in": ser.validated_data["check_in"],
                    "check_out": ser.validated_data["check_out"],
                    "source": "biometric_import",
                },
            )[0]
            created.append(obj)
        return Response(AttendanceRecordSerializer(created, many=True).data, status=201)


class PayrollRunViewSet(TenantScopedModelViewSet):
    queryset = PayrollRun.objects.prefetch_related("payslips").all()
    serializer_class = PayrollRunSerializer

    @action(detail=True, methods=["post"], url_path="generate-payslips")
    def generate_payslips(self, request, pk=None):
        run = self.get_object()
        if run.status != "draft":
            raise ValidationError("Cannot regenerate payslips on a posted run.")

        contracts = Contract.objects.filter(
            tenant_id=run.tenant_id,
            is_active=True,
            start_date__lte=run.period_end,
        ).filter(Q(end_date__isnull=True) | Q(end_date__gte=run.period_start))

        payslips = [
            compute_payslip(payroll_run=run, employee=c.employee, contract=c) for c in contracts
        ]
        return Response(PayslipSerializer(payslips, many=True).data)

    @action(detail=True, methods=["post"], url_path="post")
    def post_run(self, request, pk=None):
        run = self.get_object()
        if run.status != "draft":
            raise ValidationError(f"Payroll run is already '{run.status}'.")

        payslips = list(run.payslips.all())
        if not payslips:
            raise ValidationError("No payslips on this run — call generate-payslips first.")

        total_gross = sum((p.gross_pay for p in payslips), Decimal("0"))
        total_net = sum((p.net_pay for p in payslips), Decimal("0"))
        total_late_deduction = sum((p.late_deduction for p in payslips), Decimal("0"))

        if total_late_deduction and not run.deduction_recovery_account_id:
            raise ValidationError("Payslips have late deductions but no deduction_recovery_account set on the run.")

        gl_lines = [
            {"account": run.salary_expense_account, "debit": total_gross, "credit": 0},
            {"account": run.salary_payable_account, "debit": 0, "credit": total_net},
        ]
        if total_late_deduction:
            gl_lines.append(
                {"account": run.deduction_recovery_account, "debit": 0, "credit": total_late_deduction}
            )

        try:
            entry = post_journal_entry(
                tenant_id=run.tenant_id,
                date=run.period_end,
                reference=f"PAYROLL-{run.period_start}-{run.period_end}",
                lines=gl_lines,
                currency=run.currency,
                narration=f"Payroll run {run.period_start} to {run.period_end}",
            )
        except UnbalancedEntryError as exc:
            raise ValidationError(f"Journal entry would be unbalanced: {exc}")

        run.status = "posted"
        run.journal_entry = entry
        run.save(update_fields=["status", "journal_entry"])
        Payslip.objects.filter(payroll_run=run).update(status="posted")

        # run.payslips was prefetched by get_object()'s queryset before the
        # update above — re-fetch so the response reflects posted status,
        # not the stale prefetch cache.
        run = PayrollRun.objects.prefetch_related("payslips").get(pk=run.pk)
        return Response(PayrollRunSerializer(run).data)
