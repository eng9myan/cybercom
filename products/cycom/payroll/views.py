from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import PayrollRun, Payslip
from .serializers import PayrollRunSerializer, PayslipSerializer


class BasePayrollViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        return self.queryset.filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class PayrollRunViewSet(BasePayrollViewSet):
    queryset = PayrollRun.objects.all()
    serializer_class = PayrollRunSerializer


class PayslipViewSet(BasePayrollViewSet):
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer
