from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.discuss.views import ChannelViewSet, MessageViewSet

router = DefaultRouter()
router.register("channels", ChannelViewSet)
router.register("messages", MessageViewSet)

urlpatterns = [path("", include(router.urls))]
