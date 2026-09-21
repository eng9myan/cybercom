from rest_framework.routers import DefaultRouter

from products.cycom.appraisals.views import AppraisalViewSet

router = DefaultRouter()
router.register("appraisals", AppraisalViewSet, basename="appraisal")

urlpatterns = router.urls
