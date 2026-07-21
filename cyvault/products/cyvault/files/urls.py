from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyvault.files.views import FileObjectViewSet

router = DefaultRouter()
router.register("files", FileObjectViewSet)

urlpatterns = [path("", include(router.urls))]
