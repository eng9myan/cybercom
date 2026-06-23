from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'results', views.LabResultViewViewSet, basename='lab-result')
router.register(r'trends', views.LabResultTrendViewSet, basename='lab-result-trend')
router.register(
    r'critical-acknowledgements',
    views.CriticalResultAcknowledgementViewSet,
    basename='critical-result-acknowledgement',
)
router.register(
    r'share-links',
    views.LabResultShareLinkViewSet,
    basename='lab-result-share-link',
)

urlpatterns = [path('', include(router.urls))]
