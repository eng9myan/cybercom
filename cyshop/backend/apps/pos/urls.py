from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sessions', views.PosSessionViewSet, basename='pos-session')
router.register(r'orders', views.PosOrderViewSet, basename='pos-order')
router.register(r'payments', views.PosPaymentViewSet, basename='pos-payment')
router.register(r'receipts', views.PosReceiptViewSet, basename='pos-receipt')
router.register(r'devices', views.DeviceViewSet, basename='pos-device')

urlpatterns = [path('', include(router.urls))]
