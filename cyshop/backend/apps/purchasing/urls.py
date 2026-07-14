from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vendors', views.VendorViewSet, basename='vendor')
router.register(r'orders', views.PurchaseOrderViewSet, basename='purchase-order')
router.register(r'receipts', views.GoodsReceiptViewSet, basename='goods-receipt')

urlpatterns = [path('', include(router.urls))]
