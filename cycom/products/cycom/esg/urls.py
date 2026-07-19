from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.esg.views import EmissionEntryViewSet, EmissionFactorViewSet, EmissionReportView

router = DefaultRouter()
router.register("factors", EmissionFactorViewSet)
router.register("entries", EmissionEntryViewSet)

urlpatterns = [
    path("report/", EmissionReportView.as_view(), name="esg-report"),
    path("", include(router.urls)),
]
