from rest_framework.routers import DefaultRouter

from products.cycom.helpdesk.views import SLAPolicyViewSet, TicketViewSet

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="helpdesk-ticket")
router.register("sla-policies", SLAPolicyViewSet, basename="helpdesk-sla-policy")

urlpatterns = router.urls
