from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LeadViewSet, OpportunityViewSet, ActivityViewSet, TaskViewSet,
    MeetingViewSet, QuotationViewSet, SalesOrderViewSet, SalesCommunicationViewSet
)

router = DefaultRouter()
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'meetings', MeetingViewSet, basename='meeting')
router.register(r'quotations', QuotationViewSet, basename='quotation')
router.register(r'orders', SalesOrderViewSet, basename='order')
router.register(r'communications', SalesCommunicationViewSet, basename='communication')

urlpatterns = [
    path('', include(router.urls)),
]
