from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'invoices', views.PatientInvoiceViewSet, basename='invoice')
router.register(r'transactions', views.PaymentTransactionViewSet, basename='transaction')
router.register(r'methods', views.PaymentMethodViewSet, basename='payment-method')
router.register(r'installment-plans', views.InstallmentPlanViewSet, basename='installment-plan')

urlpatterns = [
    path('', include(router.urls)),
]
