from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("departments", views.DepartmentViewSet, basename="department")
router.register("employees", views.EmployeeViewSet, basename="employee")
router.register("attendance", views.AttendanceViewSet, basename="attendance")
router.register("leave-requests", views.LeaveRequestViewSet, basename="leave-request")
router.register(
    "performance-reviews", views.PerformanceReviewViewSet, basename="performance-review"
)

urlpatterns = router.urls
