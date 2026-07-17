from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.cyai_platform.views import AgentEntitlementViewSet, AgentListView, RouteQuestionView

router = DefaultRouter()
router.register("entitlements", AgentEntitlementViewSet)

urlpatterns = [
    path("agents/", AgentListView.as_view(), name="cyai-agents"),
    path("route/", RouteQuestionView.as_view(), name="cyai-route"),
    path("", include(router.urls)),
]
