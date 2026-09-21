from rest_framework.routers import DefaultRouter

from products.cycom.sales.views import QuotationTemplateViewSet, SalesOrderViewSet

router = DefaultRouter()
router.register("orders", SalesOrderViewSet, basename="sales-order")
router.register("quotation-templates", QuotationTemplateViewSet, basename="sales-quotation-template")

urlpatterns = router.urls
