from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.expenses.views import ExpenseViewSet

router = DefaultRouter()
router.register("expenses", ExpenseViewSet)

urlpatterns = [path("", include(router.urls))]
