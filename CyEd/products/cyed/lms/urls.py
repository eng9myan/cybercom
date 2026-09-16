from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.lms.views import CourseViewSet, LessonViewSet, ModuleViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet)
router.register("modules", ModuleViewSet)
router.register("lessons", LessonViewSet)

urlpatterns = [path("", include(router.urls))]
