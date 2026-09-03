from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.project.views import ProjectViewSet, TaskViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet)
router.register("tasks", TaskViewSet)

urlpatterns = [path("", include(router.urls))]
