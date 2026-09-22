from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.blog.views import BlogPostViewSet

router = DefaultRouter()
router.register("posts", BlogPostViewSet)

urlpatterns = [path("", include(router.urls))]
