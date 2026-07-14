from rest_framework.routers import DefaultRouter

from .views import (
    SpecimenChainOfCustodyViewSet,
    SpecimenCollectionViewSet,
    SpecimenContainerViewSet,
    SpecimenRejectionViewSet,
    SpecimenStorageViewSet,
    SpecimenTransportViewSet,
    SpecimenViewSet,
)

router = DefaultRouter()
router.register("specimens", SpecimenViewSet, basename="lab-specimens")
router.register("containers", SpecimenContainerViewSet, basename="lab-specimen-containers")
router.register("collections", SpecimenCollectionViewSet, basename="lab-specimen-collections")
router.register("transports", SpecimenTransportViewSet, basename="lab-specimen-transports")
router.register("storage", SpecimenStorageViewSet, basename="lab-specimen-storage")
router.register("rejections", SpecimenRejectionViewSet, basename="lab-specimen-rejections")
router.register("chain-of-custody", SpecimenChainOfCustodyViewSet, basename="lab-chain-of-custody")

urlpatterns = router.urls
