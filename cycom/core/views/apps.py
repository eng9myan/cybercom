from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims

# Human-readable labels for the module names app/settings/modules/page.tsx
# shows. Falls back to a title-cased version of the last path segment for
# any product app not listed here, so a new app never needs this file
# touched to show up.
_LABELS = {
    "products.cycom.company": "Multi-Company",
    "products.cycom.accounting": "Accounting & GL",
    "products.cycom.ar_ap": "AR/AP & Vendors",
    "products.cycom.hr": "HR",
    "products.cycom.payroll": "Payroll",
    "products.cycom.inventory": "Inventory & Warehouse",
    "products.cycom.catalog": "Product Catalog",
    "products.cycom.pos": "Point of Sale",
    "products.cycom.crm": "CRM",
    "products.cycom.procurement": "Procurement",
    "products.cycom.sales": "Sales",
    "products.cycom.manufacturing": "Manufacturing",
    "products.cycom.storefront": "eCommerce Storefront",
    "products.cycom.blog": "Blog",
    "products.cycom.forum": "Forum",
    "products.cycom.livechat": "Live Chat",
    "products.cycom.elearning": "eLearning",
    "products.cycom.reporting": "Custom Reports / BI",
    "products.cycom.cms": "Website Builder",
    "products.cycom.hitl": "Approvals (HITL)",
    "products.cycom.esign": "E-Signature",
    "products.cycom.documents": "Documents",
}


class InstalledAppsView(APIView):
    """
    Read-only listing of the real business modules active in this
    deployment (settings.PRODUCT_APPS). Replaces a prior fake "install a
    module from a GitHub repo" UI -- Django serves one shared app list to
    every tenant, nothing is ever installed per-tenant here, so the only
    honest thing this endpoint can do is report what's actually running.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        apps = [
            {"key": dotted, "name": _LABELS.get(dotted, dotted.rsplit(".", 1)[-1].replace("_", " ").title())}
            for dotted in getattr(settings, "PRODUCT_APPS", [])
        ]
        return Response({"apps": apps, "count": len(apps)})
