from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(
    r'types',
    views.PortalConsentTypeViewSet,
    basename='portal-consent-type',
)
router.register(
    r'records',
    views.PortalConsentRecordViewSet,
    basename='portal-consent-record',
)
router.register(
    r'requests',
    views.ConsentRequestViewSet,
    basename='portal-consent-request',
)
router.register(
    r'history',
    views.ConsentHistoryViewSet,
    basename='portal-consent-history',
)

urlpatterns = [path('', include(router.urls))]
