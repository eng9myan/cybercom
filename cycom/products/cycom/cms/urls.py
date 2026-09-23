from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.cms.views import PageBlockViewSet, PageViewSet

router = DefaultRouter()
router.register("pages", PageViewSet)
router.register("blocks", PageBlockViewSet)

urlpatterns = [path("", include(router.urls))]
