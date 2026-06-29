from rest_framework.routers import DefaultRouter

from .views import DiscountRuleViewSet, PackagePriceViewSet, PriceListViewSet, ServicePriceViewSet

router = DefaultRouter()
router.register(r"lists", PriceListViewSet, basename="price-list")
router.register(r"services", ServicePriceViewSet, basename="service-price")
router.register(r"packages", PackagePriceViewSet, basename="package-price")
router.register(r"discounts", DiscountRuleViewSet, basename="discount-rule")

urlpatterns = router.urls
