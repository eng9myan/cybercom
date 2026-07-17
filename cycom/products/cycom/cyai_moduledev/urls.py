from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.cyai_moduledev.views import ModuleDevRequestViewSet

router = DefaultRouter()
router.register("requests", ModuleDevRequestViewSet)

urlpatterns = [path("", include(router.urls))]
