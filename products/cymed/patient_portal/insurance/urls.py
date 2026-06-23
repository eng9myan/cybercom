from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'cards', views.InsuranceCardViewSet, basename='insurance-card')
router.register(r'verifications', views.CoverageVerificationViewSet, basename='coverage-verification')
router.register(r'preauths', views.PreauthorizationRequestViewSet, basename='preauth-request')
router.register(r'claims', views.ClaimStatusViewSet, basename='claim-status')

urlpatterns = [
    path('', include(router.urls)),
]
