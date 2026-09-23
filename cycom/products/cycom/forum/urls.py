from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.forum.views import ForumReplyViewSet, ForumThreadViewSet

router = DefaultRouter()
router.register("threads", ForumThreadViewSet)
router.register("replies", ForumReplyViewSet)

urlpatterns = [path("", include(router.urls))]
