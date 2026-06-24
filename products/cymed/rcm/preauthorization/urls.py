from rest_framework.routers import DefaultRouter
from .views import (
    PreauthorizationViewSet, AuthorizationRequestViewSet,
    AuthorizationDecisionViewSet, AuthorizationAppealViewSet,
)

router = DefaultRouter()
router.register(r"", PreauthorizationViewSet, basename="preauthorization")
router.register(r"requests", AuthorizationRequestViewSet, basename="auth-request")
router.register(r"decisions", AuthorizationDecisionViewSet, basename="auth-decision")
router.register(r"appeals", AuthorizationAppealViewSet, basename="auth-appeal")

urlpatterns = router.urls
