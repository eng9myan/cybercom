from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cyed.library.views import BookViewSet, LibraryPolicyViewSet, LoanViewSet

router = DefaultRouter()
router.register("books", BookViewSet)
router.register("loans", LoanViewSet)
router.register("policy", LibraryPolicyViewSet)

urlpatterns = [path("", include(router.urls))]
