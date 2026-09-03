from rest_framework.routers import DefaultRouter

from products.cycom.helpdesk.views import TicketViewSet

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="helpdesk-ticket")

urlpatterns = router.urls
