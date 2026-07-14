from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # ── Platform API v1 (shared identity/tenant/audit/events) ──────────────
    path("api/v1/tenants/", include("platform.tenant.urls")),
    path("api/v1/identity/", include("platform.cyidentity.urls")),
    path("api/v1/events/", include("platform.events.urls")),
    path("api/v1/audit/", include("platform.audit.urls")),
    path("api/v1/notifications/", include("platform.notifications.urls")),
    # ── CyMart API v1 ────────────────────────────────────────────────────────
    path("api/v1/commission/", include("products.cymart.commission.urls")),
    path("api/v1/catalog/", include("products.cymart.catalog.urls")),
    path("api/v1/marketplace/", include("products.cymart.orders.urls")),
    path("api/v1/marketplace/", include("products.cymart.cart.urls")),
    path("api/v1/settlement/", include("products.cymart.settlement.urls")),
    path("api/v1/payments/", include("products.cymart.payments.urls")),
]
