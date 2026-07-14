from rest_framework.routers import DefaultRouter

from .views import PACSEventViewSet, PACSNodeViewSet, PACSQueryViewSet, StudyRouteViewSet

router = DefaultRouter()
router.register("nodes", PACSNodeViewSet, basename="pacs-node")
router.register("queries", PACSQueryViewSet, basename="pacs-query")
router.register("routes", StudyRouteViewSet, basename="study-route")
router.register("events", PACSEventViewSet, basename="pacs-event")

urlpatterns = router.urls
