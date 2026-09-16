from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.assets.views import AssetViewSet

router = DefaultRouter()
router.register("assets", AssetViewSet)

urlpatterns = [path("", include(router.urls))]
