from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.governance.views import AuditEventViewSet, ConsentRecordViewSet

router = DefaultRouter()
router.register("audit-events", AuditEventViewSet)
router.register("consents", ConsentRecordViewSet)

urlpatterns = [path("", include(router.urls))]
