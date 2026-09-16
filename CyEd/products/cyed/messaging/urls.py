from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.messaging.views import MessageThreadViewSet, MessageViewSet

router = DefaultRouter()
router.register("threads", MessageThreadViewSet)
router.register("messages", MessageViewSet)

urlpatterns = [path("", include(router.urls))]
