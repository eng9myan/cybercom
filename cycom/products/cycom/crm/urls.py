from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.cycom.crm.views import ActivityViewSet, LeadViewSet

router = DefaultRouter()
router.register("leads", LeadViewSet)
router.register("activities", ActivityViewSet)

urlpatterns = [path("", include(router.urls))]
