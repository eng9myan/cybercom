from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.knowledge.views import ArticleViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet)

urlpatterns = [path("", include(router.urls))]
