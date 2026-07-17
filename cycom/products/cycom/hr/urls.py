from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.hr.views import ContractViewSet, EmployeeViewSet

router = DefaultRouter()
router.register("employees", EmployeeViewSet)
router.register("contracts", ContractViewSet)

urlpatterns = [path("", include(router.urls))]
