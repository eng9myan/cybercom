from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.sif.views import (
    SifCoverageView,
    SifObjectByRefIdView,
    SifObjectView,
    SifRefIdViewSet,
)

router = DefaultRouter()
router.register("refids", SifRefIdViewSet)

urlpatterns = [
    path("coverage/", SifCoverageView.as_view(), name="sif-coverage"),
    path("objects/<str:object_type>/", SifObjectView.as_view(), name="sif-objects"),
    path("refid/<str:refid>/", SifObjectByRefIdView.as_view(), name="sif-by-refid"),
    path("", include(router.urls)),
]
