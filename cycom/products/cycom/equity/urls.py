from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.equity.views import (
    DividendDistributionViewSet,
    ShareClassViewSet,
    ShareGrantViewSet,
    ShareholderViewSet,
)

router = DefaultRouter()
router.register("share-classes", ShareClassViewSet)
router.register("shareholders", ShareholderViewSet)
router.register("grants", ShareGrantViewSet)
router.register("distributions", DividendDistributionViewSet)

urlpatterns = [path("", include(router.urls))]
