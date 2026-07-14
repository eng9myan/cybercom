from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import PayrollBatch, Payslip, PayslipLine
from .serializers import PayrollBatchSerializer, PayslipSerializer, PayslipLineSerializer


class PayrollBatchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PayrollBatchSerializer

    def get_queryset(self):
        qs = PayrollBatch.objects.filter(tenant_id=self.request.tenant_id)
        batch_status = self.request.query_params.get('status')
        if batch_status:
            qs = qs.filter(status=batch_status)
        period_start = self.request.query_params.get('period_start')
        if period_start:
            qs = qs.filter(period_start__gte=period_start)
        period_end = self.request.query_params.get('period_end')
        if period_end:
            qs = qs.filter(period_end__lte=period_end)
        return qs

    @action(detail=True, methods=['post'])
    def approve_batch(self, request, pk=None):
        """Aggregate payslip totals and transition the batch to 'approved'."""
        batch = self.get_object()
        batch.update_totals()
        batch.status = 'approved'
        batch.save()
        return Response(
            PayrollBatchSerializer(batch, context={'request': request}).data
        )


class PayslipViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PayslipSerializer

    def get_queryset(self):
        qs = Payslip.objects.filter(batch__tenant_id=self.request.tenant_id)
        batch = self.request.query_params.get('batch')
        if batch:
            qs = qs.filter(batch=batch)
        employee = self.request.query_params.get('employee')
        if employee:
            qs = qs.filter(employee=employee)
        slip_status = self.request.query_params.get('status')
        if slip_status:
            qs = qs.filter(status=slip_status)
        return qs.select_related('batch', 'employee')


class PayslipLineViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PayslipLineSerializer

    def get_queryset(self):
        qs = PayslipLine.objects.filter(
            payslip__batch__tenant_id=self.request.tenant_id
        )
        payslip = self.request.query_params.get('payslip')
        if payslip:
            qs = qs.filter(payslip=payslip)
        line_type = self.request.query_params.get('line_type')
        if line_type:
            qs = qs.filter(line_type=line_type)
        return qs.select_related('payslip')
