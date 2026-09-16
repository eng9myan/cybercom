from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.intake.views import DocumentIntakeViewSet

router = DefaultRouter()
router.register("documents", DocumentIntakeViewSet)

urlpatterns = [path("", include(router.urls))]
