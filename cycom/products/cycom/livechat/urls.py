from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.livechat.views import ChatSessionViewSet

router = DefaultRouter()
router.register("sessions", ChatSessionViewSet)

urlpatterns = [path("", include(router.urls))]
