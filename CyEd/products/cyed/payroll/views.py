from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsFinanceOrLeadership
from products.cyed.hr.models import Contract, Staff
from products.cyed.payroll.models import PayrollRun, Payslip, PayslipLine, SalaryComponent
from products.cyed.payroll.serializers import (
    PayrollRunSerializer, PayslipSerializer, SalaryComponentSerializer,
)
from products.cyed.payroll.services import attendance_for_period, compute_payslip
from products.cyed.security.stepup import RequiresRecentMfa


class PayrollRunViewSet(TenantScopedModelViewSet):
    queryset = PayrollRun.objects.prefetch_related("payslips").all()
    serializer_class = PayrollRunSerializer
    permission_classes = [IsFinanceOrLeadership]

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """
        Generate a payslip for every active staff member with a current contract.
        When the run has a period, Staff Attendance is consulted so unexplained
        absences are docked and every figure is written as an itemised line.
        """
        run = self.get_object()
        if run.status == "paid":
            return Response({"detail": "A paid run cannot be reprocessed."},
                            status=status.HTTP_400_BAD_REQUEST)
        run.payslips.all().delete()  # cascades to lines

        created = 0
        skipped = []
        for staff in Staff.objects.filter(tenant_id=run.tenant_id, is_active=True):
            contract = Contract.objects.filter(tenant_id=run.tenant_id, staff=staff, is_current=True).first()
            if not contract:
                skipped.append({"staff": str(staff.id),
                                "name": f"{staff.first_name} {staff.last_name}",
                                "reason": "no current contract"})
                continue
            calc = compute_payslip(
                staff=staff, contract=contract, tenant_id=run.tenant_id,
                period_start=run.period_start, period_end=run.period_end,
            )
            lines = calc.pop("lines", [])
            slip = Payslip.objects.create(
                tenant_id=run.tenant_id, payroll_run=run, staff=staff, **calc
            )
            for ln in lines:
                PayslipLine.objects.create(tenant_id=run.tenant_id, payslip=slip, **ln)
            created += 1

        run.status = "processed"
        run.save(update_fields=["status", "updated_at"])
        data = self.get_serializer(run).data
        data["payslips_created"] = created
        data["skipped"] = skipped  # never silently drop staff — surface who and why
        return Response(data)

    @action(detail=True, methods=["post"], url_path="mark-paid",
            permission_classes=[IsFinanceOrLeadership, RequiresRecentMfa])
    def mark_paid(self, request, pk=None):
        """Record payment of every payslip in the run (payment history)."""
        run = self.get_object()
        if run.status != "processed":
            return Response({"detail": "Only a processed run can be marked paid."}, status=400)
        paid_on = request.data.get("paid_on") or timezone.localdate().isoformat()
        reference = request.data.get("reference", "")
        updated = run.payslips.update(
            payment_status="paid", paid_on=paid_on, payment_reference=reference
        )
        run.status = "paid"
        run.pay_date = paid_on
        run.save(update_fields=["status", "pay_date", "updated_at"])
        return Response({"run": str(run.id), "payslips_paid": updated, "paid_on": paid_on})

    @action(detail=True, methods=["get"])
    def reconcile(self, request, pk=None):
        """
        Reconcile the run against Staff Attendance: for each payslip, compare the
        hours/absences the payslip was built from with what attendance now holds.
        Any drift means attendance changed after processing — reprocess the run.
        """
        run = self.get_object()
        if not (run.period_start and run.period_end):
            return Response({"detail": "Set period_start and period_end on the run to reconcile."}, status=400)
        rows, drift = [], 0
        for slip in run.payslips.select_related("staff"):
            att = attendance_for_period(run.tenant_id, slip.staff, run.period_start, run.period_end)
            mismatch = (
                Decimal(slip.hours_worked) != att["hours_worked"]
                or Decimal(slip.unpaid_days) != att["unpaid_days"]
            )
            if mismatch:
                drift += 1
            rows.append({
                "staff": str(slip.staff_id),
                "name": f"{slip.staff.first_name} {slip.staff.last_name}",
                "payslip_hours": str(slip.hours_worked),
                "attendance_hours": str(att["hours_worked"]),
                "payslip_unpaid_days": str(slip.unpaid_days),
                "attendance_unpaid_days": str(att["unpaid_days"]),
                "days_recorded": att["days_recorded"],
                "in_sync": not mismatch,
            })
        return Response({
            "run": str(run.id), "period": run.period_label,
            "payslips": len(rows), "out_of_sync": drift,
            "reconciled": drift == 0, "rows": rows,
        })


class PayslipViewSet(TenantScopedModelViewSet):
    queryset = Payslip.objects.select_related("staff", "payroll_run").prefetch_related("lines").all()
    serializer_class = PayslipSerializer
    permission_classes = [IsFinanceOrLeadership]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        run = self.request.query_params.get("payroll_run")
        staff = self.request.query_params.get("staff")
        if run:
            qs = qs.filter(payroll_run_id=run)
        if staff:
            qs = qs.filter(staff_id=staff)
        if self.request.query_params.get("payment_status"):
            qs = qs.filter(payment_status=self.request.query_params["payment_status"])
        return qs

    @action(detail=True, methods=["post"], url_path="mark-paid",
            permission_classes=[IsFinanceOrLeadership, RequiresRecentMfa])
    def mark_paid(self, request, pk=None):
        slip = self.get_object()
        slip.payment_status = "paid"
        slip.paid_on = request.data.get("paid_on") or timezone.localdate()
        slip.payment_reference = request.data.get("reference", "")
        slip.save()
        return Response(PayslipSerializer(slip).data)


class SalaryComponentViewSet(TenantScopedModelViewSet):
    queryset = SalaryComponent.objects.select_related("staff").all()
    serializer_class = SalaryComponentSerializer
    permission_classes = [IsFinanceOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("staff"):
            qs = qs.filter(staff_id=self.request.query_params["staff"])
        if self.request.query_params.get("kind"):
            qs = qs.filter(kind=self.request.query_params["kind"])
        return qs
