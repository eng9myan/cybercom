from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.learning_bridge.views import (
    FamilyResourceViewSet,
    LearningBridgeSummaryView,
    OfflineActivityPackViewSet,
)

router = DefaultRouter()
router.register("resources", FamilyResourceViewSet)
router.register("offline-packs", OfflineActivityPackViewSet)

urlpatterns = [
    path("summary/", LearningBridgeSummaryView.as_view(), name="learning-bridge-summary"),
    path("", include(router.urls)),
]
