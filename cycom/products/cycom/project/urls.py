from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.project.views import ProjectViewSet, TaskViewSet, TimesheetEntryViewSet

router = DefaultRouter()
router.register("projects", ProjectViewSet)
router.register("tasks", TaskViewSet)
router.register("timesheets", TimesheetEntryViewSet)

urlpatterns = [path("", include(router.urls))]
