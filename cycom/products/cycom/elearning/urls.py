from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.elearning.views import CourseViewSet, EnrollmentViewSet, LessonViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet)
router.register("lessons", LessonViewSet)
router.register("enrollments", EnrollmentViewSet, basename="enrollment")

urlpatterns = [path("", include(router.urls))]
