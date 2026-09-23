from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cycom.reporting.models import SavedReport
from products.cycom.reporting.registry import dimension_choices, measure_choices, source_choices
from products.cycom.reporting.serializers import SavedReportSerializer
from products.cycom.reporting.services import run_report


class SavedReportViewSet(TenantScopedModelViewSet):
    queryset = SavedReport.objects.all()
    serializer_class = SavedReportSerializer

    @action(detail=True, methods=["get"])
    def run(self, request, pk=None):
        report = self.get_object()
        return Response(run_report(report, request.tenant_id))


@api_view(["GET"])
@permission_classes([IsAuthenticatedViaClaims])
def report_sources_meta(request):
    """Drives the report builder UI: every source's label plus its allowed
    dimensions/measures, straight from the same whitelist run_report()
    enforces server-side."""
    return Response(
        [
            {
                "key": key,
                "label": label,
                "dimensions": [{"key": k, "label": lbl} for k, lbl in dimension_choices(key)],
                "measures": [{"key": k, "label": lbl} for k, lbl in measure_choices(key)],
            }
            for key, label in source_choices()
        ]
    )
