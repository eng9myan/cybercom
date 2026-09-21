from rest_framework.routers import DefaultRouter

from products.cycom.referrals.views import ReferralViewSet

router = DefaultRouter()
router.register("referrals", ReferralViewSet, basename="referral")

urlpatterns = router.urls
