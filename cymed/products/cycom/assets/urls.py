from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("items", views.AssetViewSet, basename="asset")
router.register("depreciations", views.AssetDepreciationViewSet, basename="asset-depreciation")

urlpatterns = router.urls
