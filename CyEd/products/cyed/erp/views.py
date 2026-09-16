from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from products.cyed.erp import client
from products.cyed.governance.access import IsStaff


class ErpProxyView(APIView):
    """
    Proxy to CyCom's generic ERP (HR/payroll/inventory/procurement/fleet/finance).
    GET/POST /api/v1/erp/<cycom-path>/  — staff only; forwards the caller's token.
    """

    permission_classes = [IsStaff]

    def _forward(self, request, path, method):
        if not client.is_allowed(path):
            return Response({"detail": f"Resource '{path}' is not a permitted ERP resource."},
                            status=status.HTTP_400_BAD_REQUEST)
        token = ""
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
        try:
            code, data = client.fetch(
                path, token=token, tenant_id=getattr(request, "tenant_id", "") or "",
                method=method, body=(request.data if method == "POST" else None),
            )
        except client.CycomNotConfigured as e:
            return Response({"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except client.CycomError as e:
            return Response(e.detail if isinstance(e.detail, dict) else {"detail": e.detail}, status=e.status)
        return Response(data, status=code)

    def get(self, request, path):
        return self._forward(request, path, "GET")

    def post(self, request, path):
        return self._forward(request, path, "POST")
