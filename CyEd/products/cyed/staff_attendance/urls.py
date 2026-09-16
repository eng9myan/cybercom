from rest_framework.routers import DefaultRouter

from products.cyed.staff_attendance.views import StaffAttendanceDayViewSet, TimesheetViewSet

router = DefaultRouter()
router.register("days", StaffAttendanceDayViewSet, basename="staff-attendance-day")
router.register("timesheets", TimesheetViewSet, basename="timesheet")

urlpatterns = router.urls
