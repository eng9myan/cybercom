from rest_framework.routers import DefaultRouter

from .views import (
    AuthorizationAppealViewSet,
    AuthorizationDecisionViewSet,
    AuthorizationRequestViewSet,
    PreauthorizationViewSet,
)

router = DefaultRouter()
router.register(r"", PreauthorizationViewSet, basename="preauthorization")
router.register(r"requests", AuthorizationRequestViewSet, basename="auth-request")
router.register(r"decisions", AuthorizationDecisionViewSet, basename="auth-decision")
router.register(r"appeals", AuthorizationAppealViewSet, basename="auth-appeal")

urlpatterns = router.urls
