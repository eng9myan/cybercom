from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.school.notice_views import NoticeViewSet
from products.cyed.school.views import SchoolLogoView, SchoolProfileView

router = DefaultRouter()
router.register("notices", NoticeViewSet)

urlpatterns = [
    path("profile/", SchoolProfileView.as_view(), name="school-profile"),
    path("logo/", SchoolLogoView.as_view(), name="school-logo"),
    path("", include(router.urls)),
]
