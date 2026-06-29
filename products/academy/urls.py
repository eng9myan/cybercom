from rest_framework.routers import DefaultRouter

from .views import (
    CertificateViewSet,
    CourseModuleViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    ExamAttemptViewSet,
    ExamViewSet,
    LearningPathViewSet,
)

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("modules", CourseModuleViewSet, basename="course-module")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
router.register("exams", ExamViewSet, basename="exam")
router.register("exam-attempts", ExamAttemptViewSet, basename="exam-attempt")
router.register("certificates", CertificateViewSet, basename="certificate")
router.register("learning-paths", LearningPathViewSet, basename="learning-path")

urlpatterns = router.urls
