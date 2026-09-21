from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.company.views import CompanyViewSet

router = DefaultRouter()
router.register("companies", CompanyViewSet)

urlpatterns = [path("", include(router.urls))]
