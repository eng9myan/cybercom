from django.urls import path
from rest_framework.routers import DefaultRouter

from products.cyed.org.views import CampusViewSet, GroupRollupView

router = DefaultRouter()
router.register("campuses", CampusViewSet, basename="campus")

urlpatterns = [
    path("rollup/", GroupRollupView.as_view(), name="org-rollup"),
]
urlpatterns += router.urls
