from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.todo.views import TaskViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet)

urlpatterns = [path("", include(router.urls))]
