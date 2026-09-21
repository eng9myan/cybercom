from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.marketing.views import CampaignViewSet, MarketingRecipientViewSet

router = DefaultRouter()
router.register("campaigns", CampaignViewSet)
router.register("recipients", MarketingRecipientViewSet)

urlpatterns = [path("", include(router.urls))]
