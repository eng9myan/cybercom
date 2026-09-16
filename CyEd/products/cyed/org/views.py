from decimal import Decimal

from rest_framework.response import Response
from rest_framework.views import APIView

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff, PASTORAL_OR_LEADERSHIP, has_any, ADMIN, LEADERSHIP
from products.cyed.org.models import Campus
from products.cyed.org.serializers import CampusSerializer


class CampusViewSet(TenantScopedModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer

    def get_permissions(self):
        from core.permissions import IsAuthenticatedViaClaims
        return [IsAuthenticatedViaClaims()] if self.action in ("list", "retrieve") else [IsStaff()]


class GroupRollupView(APIView):
    """
    GET /api/v1/org/rollup/ — consolidated group view across campuses:
    per-campus student/staff/class counts + outstanding fees, plus group totals.
    Leadership / group-office only.
    """

    def get_permissions(self):
        from core.permissions import IsAuthenticatedViaClaims
        return [IsAuthenticatedViaClaims()]

    def get(self, request):
        if not has_any(request, ADMIN | LEADERSHIP):
            from rest_framework import status
            return Response({"detail": "Group rollup is leadership/office only."},
                            status=status.HTTP_403_FORBIDDEN)
        tenant = request.tenant_id
        from django.db.models import Sum
        from products.cyed.billing.models import Installment
        from products.cyed.hr.models import Staff
        from products.cyed.sis.models import ClassSection, Student

        campuses = list(Campus.objects.filter(tenant_id=tenant))
        rows = []
        g_students = g_staff = g_classes = 0
        g_outstanding = Decimal("0")
        for c in campuses:
            students = Student.objects.filter(tenant_id=tenant, campus=c).count()
            staff = Staff.objects.filter(tenant_id=tenant, campus=c).count()
            classes = ClassSection.objects.filter(tenant_id=tenant, campus=c).count()
            billed = Installment.objects.filter(tenant_id=tenant, bill__campus=c).exclude(status="paid") \
                .aggregate(t=Sum("amount_due"))["t"] or Decimal("0")
            rows.append({"campus": str(c.id), "name": c.name, "state": c.state,
                         "students": students, "staff": staff, "classes": classes,
                         "fees_outstanding": f"{billed:.2f}"})
            g_students += students
            g_staff += staff
            g_classes += classes
            g_outstanding += billed

        unassigned = Student.objects.filter(tenant_id=tenant, campus__isnull=True).count()
        return Response({
            "campuses": rows,
            "group_totals": {
                "campuses": len(campuses), "students": g_students, "staff": g_staff,
                "classes": g_classes, "fees_outstanding": f"{g_outstanding:.2f}",
                "students_unassigned_campus": unassigned,
            },
        })
